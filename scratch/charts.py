from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/small_medium_merged.csv")


# Histogram 1: Trip duration
# Insight: Shows typical trip time and long trips
df["Average Trip Minutes"] = df["Average Trip Seconds"] / 60

plt.figure()
plt.hist(df["Average Trip Minutes"], bins=40)
plt.title("Trip Duration Distribution")
plt.xlabel("Average Trip Minutes")
plt.ylabel("Frequency")
plt.xticks(range(0, int(df["Average Trip Minutes"].max()) + 5, 5))
plt.show() 


# Histogram 2: Trip distance
# Insight: Short vs long trips
plt.figure()
plt.hist(df["Float Trip Miles"], bins=40)
plt.title("Trip Distance Distribution")
plt.xlabel("Trip Miles")
plt.ylabel("Frequency")
plt.xticks(range(0, int(df["Float Trip Miles"].max()) + 5, 5))
plt.show()


# Histogram 3: Trip total cost
# Insight: Most common fare range and expensive outliers
plt.figure()
plt.hist(df["Average Trip Total"], bins=40)
plt.title("Trip Cost Distribution")
plt.xlabel("Average Trip Total ($)")
plt.ylabel("Frequency")
plt.xticks(range(0, int(df["Average Trip Total"].max()) + 5, 5))
plt.show()


# Histogram 4: Start hour
# Insight: When trips happen (rush hour vs night)
hour_counts = df.groupby("start_hour")["Count"].sum()

plt.figure()
plt.bar(hour_counts.index, hour_counts.values)
plt.title("Trips by Start Hour")
plt.xlabel("Start Hour")
plt.ylabel("Number of Trips")
plt.show()


# Comparison: Weekday vs Weekend trip counts
# Insight: Shows which day type has more rides overall
weekday_count = df[df["day_type"] == 0]["Count"].sum()  # Sum trips using Count column
weekend_count = df[df["day_type"] == 1]["Count"].sum()  # Sum trips using Count column

plt.figure()
plt.bar(["Weekday", "Weekend"], [weekday_count, weekend_count])
plt.title("Trip Count: Weekday vs Weekend")
plt.xlabel("Day Type")
plt.ylabel("Number of Trips")
plt.show()