from src.analytics.peer import PeerEngine


def main():
    engine = PeerEngine()

    percentiles = engine.run()

    print(
        f"Peer percentile computation completed: "
        f"{len(percentiles)} records."
    )


if __name__ == "__main__":
    main()
