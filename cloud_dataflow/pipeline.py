import argparse
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.gcp.internal.clients import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'PUT Service Account HERE'


project_id = '' # project id 
dataset_id = '' # dataset name
tableid = '' # table name
table = bigquery.TableReference(
        projectId=project_id,
        datasetId=dataset_id,
        tableId=tableid)

# Table Schema Example
table_schema = {
  "fields" :[
  {
    "name": "unique_key",
    "mode": "NULLABLE",
    "type": "STRING",
    "description": None,
    "fields": []
  },
  {
    "name": "trip_seconds",
    "mode": "NULLABLE",
    "type": "FLOAT",
    "description": None,
    "fields": []
  },
  {
    "name": "trip_miles",
    "mode": "NULLABLE",
    "type": "FLOAT",
    "description": None,
    "fields": []
  },
  {
    "name": "pickup_community_area",
    "mode": "NULLABLE",
    "type": "FLOAT",
    "description": None,
    "fields": []
  },
  {
    "name": "dropoff_community_area",
    "mode": "NULLABLE",
    "type": "FLOAT",
    "description": None,
    "fields": []
  },
  {
    "name": "fare",
    "mode": "NULLABLE",
    "type": "FLOAT",
    "description": None,
    "fields": []
  },
  {
    "name": "tolls",
    "mode": "NULLABLE",
    "type": "FLOAT",
    "description": None,
    "fields": []
  },
  {
    "name": "extras",
    "mode": "NULLABLE",
    "type": "FLOAT",
    "description": None,
    "fields": []
  },
  {
    "name": "tips",
    "mode": "NULLABLE",
    "type": "FLOAT",
    "description": None,
    "fields": []
  },
  ]
}

class ReadDataFromGCSANDPreproces(beam.DoFn):
    def __init__(self):
        pass
    def process(self, elem):
        import pandas as pd
        from google.cloud import storage
        gcs_path = elem['gcs_path']
        bucket_name = gcs_path.split('gs://')[-1].split('/')[0]
        blob_path = gcs_path.split('gs://')[-1].split('/')[1:]
        if len(blob_path) >= 1:
            blob_path = '/'.join(blob_path)
        # Initialise a client
        storage_client = storage.Client("INPUT PROJECT ID HERE")
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.download_to_filename(blob_path)
        df = pd.read_csv(blob_path)
        df.fillna(0, inplace=True)
        df.drop(df[(df['trip_seconds']>0)&(df['trip_miles']>0.0)&(df['trip_total']==0.0)].index, inplace = True)
        df.drop(df[(df['trip_seconds']==0) & (df['trip_miles']==0.0)&(df['trip_total']>0.0)].index, inplace = True)
        df.drop(df[(df['trip_seconds']==0) & (df['trip_miles']==0.0)&(df['trip_total']==0.0)].index, inplace = True)
        df = df[df['extras']<1000]
        selected_columns = ['unique_key', 'trip_seconds','trip_miles','pickup_community_area','dropoff_community_area','fare','tolls','extras','tips']
        data = pd.DataFrame(df, columns=selected_columns)
        df_json = data.to_dict('records')
        for i in range(len(df_json)):
            yield df_json[i]
    
def run(argv=None):
    """The main function which creates the pipeline and runs it."""

    parser = argparse.ArgumentParser()

    class ParameterOptions(PipelineOptions):
        @classmethod
        def _add_argparse_args(cls, parser):
            parser.add_argument(
                '--input',
                dest='input',
                default='FILL with file csv in GS Path',
                help='Path of the file to read from')
            parser.add_argument('--output',
                dest='output',
                help='Output BQ table to write results to.',
                default='Bigquery dataset.table')

    parser.add_argument('--experiments',
                        required=False,
                        dest='experiments',
                        help='experiments',
                        default='use_runner_v2')
    
    parser.add_argument('--requirements_file',
                    dest='requirements_file',
                    required=False,
                    help='Reqs',
                    default='FILL with requirements.txt')

    # Parse arguments from the command line.
    known_args, pipeline_args = parser.parse_known_args(argv)
    pipeline_options = PipelineOptions(pipeline_args)
    p = beam.Pipeline(options=pipeline_options)

    parameter_options = pipeline_options.view_as(ParameterOptions)

    (p
     | 'Read GCS Path' >> beam.Create([{"gcs_path": parameter_options.input}])
     | 'Read Raw Data From GCS and Preprocessing' >> beam.ParDo(ReadDataFromGCSANDPreproces())
     | "Reshuffle" >> beam.util.Reshuffle()
     | "Write to BQ" >> beam.io.WriteToBigQuery(
        table,
        schema = table_schema,
        write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
      )
    )
    p.run().wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()