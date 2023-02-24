import boto3
# TODO: add exceptions or remove unused import
import botocore.exceptions
from botocore.config import Config
import json
import logging
import os
from pymediainfo import MediaInfo
from typing import cast

log = logging.getLogger()
log.setLevel(logging.INFO)

aws_region = os.environ["AWS_REGION"]


def get_signed_url(expires_in, bucket, key):
    """
    Generate a signed URL
    * param expires_in:  URL Expiration time in seconds
    * param bucket:      S3 Bucket name
    * param key:         S3 Key name
    * return:            Signed URL
    """
    s3_cli = boto3.client("s3", region_name=aws_region, config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}))
    presigned_url = s3_cli.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_in)
    return presigned_url


def lambda_handler(event, context):
    """Process MediaInfo process requests received via SQS

    Returns:

    """
    # MediaInfo library location in AWS Lambda layer
    pymediainfo_library_file = "/opt/libmediainfo.so"

    s3_bucket_name = os.environ["BUCKET_NAME"]
    s3_bucket_prefix = os.environ["BUCKET_PREFIX"]
    log.info(f"\nBucket name: {s3_bucket_name}\nBucket prefix: {s3_bucket_prefix}")

    # maximum number of iterations limited by batch size, default: 10
    for record in event["Records"]:
        # get MediaInfo request from SQS message body
        mediainfo_request = json.loads(record["body"])
        # get S3 bucket name and object key from MediaInfo request
        bucket_name = mediainfo_request.get("bucket")
        key = mediainfo_request.get("key")
        log.info(f"Media file to analyze: {bucket_name}/{key}")
        # get presigned S3 URL
        signed_url = get_signed_url(300, bucket_name, key)
        # get MediaInfo report directly from S3
        mediainfo_result = cast(dict, MediaInfo.parse(signed_url, library_file=pymediainfo_library_file))
        mediainfo_data = mediainfo_result.to_data()
        analyzed_complete_name = mediainfo_data["tracks"][0].get("complete_name")
        analyzed_file_name_extension = mediainfo_data["tracks"][0].get("file_name_extension")
        analyzed_file_type = mediainfo_data["tracks"][0].get("internet_media_type")
        log.info(f"Saved MediaInfo result for {analyzed_complete_name} ({analyzed_file_type})")

        # save MediaInfo to an S3 object
        try:
            s3_client = boto3.client("s3")
            s3_client.put_object(
                Body=str(mediainfo_result.to_json()),
                Bucket=s3_bucket_name,
                Key=f"{s3_bucket_prefix}/{analyzed_file_name_extension}.mediainfo.json"
            )
        except Exception as ex:
            log.error(f"Failed to write MediaInfo result to S3: {ex}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": (f"MediaInfo ran successfully with results saved to s3://{s3_bucket_name}/{s3_bucket_prefix}")
        })
    }
