# batch-sam-mediainfo

## Getting started

First we will need to create our zip directory to be used in our AWS Lambda layer. To do that, run these two Docker commands:
```bash
docker build --tag=pymediainfo-layer-factory:latest . --no-cache
```
```bash
docker run --rm -it -v $(pwd):/data pymediainfo-layer-factory cp /packages/pymediainfo-layer.zip /data
```
Next, we will need to build our AWS Serverless Application Model (AWS SAM) application:
```bash
sam build
```
Finally, we will have to deploy our AWS SAM application to our account:
```bash
sam deploy --guided
```

Running ```sam deploy``` with the ```--guided``` flag will prompt you for a few input parameters that AWS SAM needs.
- **Stack Name:** enter the name you would like your AWS CloudFormation stack to have.
- **AWS Region:** enter the region in which you would like your CloudFormation stack to be deployed to.
- **Parameter Stage:** enter the production environment you will be deploying to. This parameter is appended to the name of resources that are created.
- The next four parameters are the S3 bucket and prefix of your content and output buckets
- **Confirm changes before deploy:** This will prompt you to approve or deny any changes that AWS SAM is going to make to your stack before deploying those changes
- **Allow SAM CLI IAM role creation:** We will need to explicitly give AWS SAM permission here to create the required IAM roles for our two Lambda functions
- **Disable rollback:** Either enable rollback on CloudFormation Create/Update failure or disable rollback
- **Same arguments to configuration file:** If you would like to save these args to a config file, so we can run ```sam deploy``` in the future instead of ```sam deploy --guided``` enter Y here
- **SAM configuration file:** the name of the file where the arguments will be saved. It is samconfig.toml by default
- **SAM configuration environment:** If you do not want to use the AWS credentials stored as default in your AWS credentials profile, enter the name of the profile you would like to use here

Now we need to invoke our Lambda procuder function. We can do that by either logging into the console or with the following command:
```bash
aws lambda invoke --region [REPLACE REGION] --function-name [REPLACE FUNCTION NAME] --payload {} response.json
```
**Make sure you replace the function name with the name of your producer function, not including the brackets**

**Make sure you also replace the region with the region of your choosing, not including the brackets**