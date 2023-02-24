import json
import os
import boto3
import botocore.exceptions
import logging

log = logging.getLogger()
log.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Generate SQS message to trigger MediaInfo analysis for media files
    with a file extension in the specified list

    Returns:
        dict: MediaInfo batch request result
    """
    queue_url = os.environ["INGEST_QUEUE"]

    s3_bucket_name = os.environ["BUCKET_NAME"]
    s3_bucket_prefix = os.environ["BUCKET_PREFIX"]
    log.info(f"\nBucket name: {s3_bucket_name}\nBucket prefix: {s3_bucket_prefix}\nQueue URL: {queue_url}")

    analyze_file_extensions = [".mp4", ".mxf", ".mov", ".wav", ".stl", ".scc"]
    log.info(f"\nAnalyze objects with file extensions: {analyze_file_extensions}")

    s3_client = boto3.client("s3")
    s3_object_list = []
    try:
        s3_paginator = s3_client.get_paginator("list_objects_v2")
        s3_operation_parameters = {
            "Bucket": s3_bucket_name,
            "Prefix": s3_bucket_prefix
        }
        s3_page_iterator = s3_paginator.paginate(**s3_operation_parameters)
        for s3_page in s3_page_iterator:
            if s3_page["KeyCount"] > 0:
                for s3_object_key in s3_page["Contents"]:
                    s3_object_key = s3_object_key["Key"]
                    orig_file_extension = os.path.splitext(s3_object_key)[1]
                    if orig_file_extension in analyze_file_extensions:
                        s3_object_list.append(s3_object_key)
                    else:
                        log.info(f"{s3_object_key} was not a supported file format.")
            else:
                log.info(f"No S3 objects found in s3://{s3_bucket_name}/{s3_bucket_prefix}")
    except botocore.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "404":
            log.info("The object does not exist.")
        else:
            raise

    sqs_client = boto3.client("sqs")
    if s3_object_list:
        for s3_object_key in s3_object_list:
            mediainfo_request = {
                "bucket": s3_bucket_name,
                "key": s3_object_key
            }
            log.info(f'MediaInfo request for {s3_bucket_name}/{s3_object_key}')
            try:
                response = sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(mediainfo_request)
                )
                log.info(f'Response from sqs send: {response}')
            except Exception as err:
                log.info(f"exception: {err}")
    else:
        log.error("Response empty and uncaught by exception.")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Batch MediaInfo run successfully",
        }),
    }
