from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, unbase64, base64, split
from pyspark.sql.types import StructField, StructType, StringType, BooleanType, ArrayType, DateType

# TO-DO: using the spark application object, read a streaming dataframe from the Kafka topic stedi-events as the source
# Be sure to specify the option that reads all the events from the topic including those that were published before you started the spark stream
# TO-DO: create a StructType for the Kafka stedi-events topic which has the Customer Risk JSON that comes from Redis- before Spark 3.0.0, schema inference is not automatic
customerRiskSchema = StructType(
    [
        StructField("customer", StringType()),
        StructField("score", StringType()),
        StructField("riskDate", StringType())
    ]
)
spark = SparkSession.builder.appName("stedi-events").getOrCreate()
spark.sparkContext.setLogLevel("WARN")
stediEventsRawStreaming = spark.readStream\
    .format("kafka")\
    .option("kafka.bootstrap.servers", "kafka:19092")\
    .option("subscribe", "stedi-events")\
    .option("startingOffsets", "earliest")\
    .load()
# TO-DO: cast the value column in the streaming dataframe as a STRING 
stediEventsStreaming = stediEventsRawStreaming.selectExpr("cast(key as string) as key", "cast(value as  string) as value")
# TO-DO: parse the JSON from the single column "value" with a json object in it, like this:
# +------------+
# | value      |
# +------------+
# |{"custom"...|
# +------------+
#
# and create separated fields like this:
# +------------+-----+-----------+
# |    customer|score| riskDate  |
# +------------+-----+-----------+
# |"sam@tes"...| -1.4| 2020-09...|
# +------------+-----+-----------+
#
# storing them in a temporary view called CustomerRisk
stediEventsStreaming.withColumn("value", from_json("value", customerRiskSchema))\
    .select(col("value.*"))\
    .createOrReplaceTempView("CustomerRisk")
# TO-DO: execute a sql statement against a temporary view, selecting the customer and the score from the temporary view, creating a dataframe called customerRiskStreamingDF
# TO-DO: sink the customerRiskStreamingDF dataframe to the console in append mode
# 
# It should output like this:
#
# +--------------------+-----
# |customer           |score|
# +--------------------+-----+
# |Spencer.Davis@tes...| 8.0|
# +--------------------+-----
# Run the python script by running the command from the terminal:
# /home/workspace/submit-event-kafka-streaming.sh
# Verify the data looks correct 
customerRiskStreamingDF = spark.sql("select customer, score from CustomerRisk")

customerRiskStreamingDF.writeStream\
    .outputMode("append")\
    .format("console")\
    .start()\
    .awaitTermination()