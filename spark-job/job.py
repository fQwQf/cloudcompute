import os
from datetime import datetime, timezone
from uuid import uuid4

from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, lit, round as spark_round, sum as spark_sum, when


def main() -> None:
    spark = (
        SparkSession.builder.appName("CloudCostLab-openGauss-analytics")
        .config("spark.sql.session.timeZone", "Asia/Shanghai")
        .getOrCreate()
    )

    jdbc_url = os.getenv("SPARK_JDBC_URL", "jdbc:postgresql://opengauss:5432/postgres")
    output_table = os.getenv("SPARK_OUTPUT_TABLE", "analytics_snapshots")
    properties = {
        "user": os.getenv("SPARK_DB_USER", "gaussdb"),
        "password": os.getenv("SPARK_DB_PASSWORD", "CloudGauss@2026"),
        "driver": os.getenv("SPARK_DB_DRIVER", "org.postgresql.Driver"),
    }

    resources = spark.read.jdbc(jdbc_url, "cloud_resources", properties=properties)
    usage_records = spark.read.jdbc(jdbc_url, "usage_records", properties=properties)

    joined = usage_records.join(resources, usage_records.resource_id == resources.id, "left")
    region_costs = (
        joined.groupBy("region")
        .agg(spark_sum("estimated_cost").alias("region_cost"))
        .orderBy(col("region_cost").desc())
        .limit(1)
        .collect()
    )
    top_region = region_costs[0]["region"] if region_costs else "-"

    aggregate = joined.agg(
        spark_round(spark_sum("estimated_cost"), 2).alias("total_cost"),
        spark_round(avg("utilization_score"), 1).alias("avg_utilization_score"),
        spark_round(spark_sum("carbon_kg"), 2).alias("carbon_kg"),
    ).collect()[0]

    resource_count = resources.count()
    active_count = resources.filter(col("status") == "active").count()
    budget_usage = (
        joined.groupBy(resources.id, "monthly_budget")
        .agg(spark_sum("estimated_cost").alias("used_cost"))
        .withColumn(
            "is_risk",
            when((col("monthly_budget") > 0) & (col("used_cost") / col("monthly_budget") >= 0.8), 1).otherwise(0),
        )
    )
    risk_count = budget_usage.agg(spark_sum("is_risk").alias("risk_count")).collect()[0]["risk_count"] or 0

    snapshot = spark.createDataFrame(
        [
            (
                str(uuid4()),
                datetime.now(timezone.utc),
                int(resource_count),
                int(active_count),
                float(aggregate["total_cost"] or 0),
                float(aggregate["avg_utilization_score"] or 0),
                float(aggregate["carbon_kg"] or 0),
                top_region,
                int(risk_count),
                "spark",
            )
        ],
        [
            "id",
            "snapshot_time",
            "resource_count",
            "active_count",
            "total_cost",
            "avg_utilization_score",
            "carbon_kg",
            "top_region",
            "risk_count",
            "generated_by",
        ],
    )

    snapshot.write.jdbc(jdbc_url, output_table, mode="append", properties=properties)
    spark.stop()


if __name__ == "__main__":
    main()
