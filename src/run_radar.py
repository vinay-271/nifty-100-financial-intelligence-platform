from src.analytics.radar import RadarChartEngine


def main():
    engine = RadarChartEngine()

    charts = engine.generate_all()

    print(
        f"Radar chart generation completed: "
        f"{len(charts)} charts."
    )


if __name__ == "__main__":
    main()
