import requests


def send_to_discord(df, webhook_url):
    """
    Send new Data Engineer jobs to Discord.
    """

    # Keep only Data Engineer jobs
    de_jobs = df[df["job_group"].isin(["Data Engineer", "Business Analyst", "Data Analyst"])]

    if de_jobs.empty:
        print("No new Data Engineer jobs to send.")
        return

    for _, job in de_jobs.iterrows():

        message = (
            f"🚀 **{job['job_title']}**\n"
            f"🏢 {job['company']}\n"
            f"📍 {job['city']}\n"
            f"💰 {job['min_salary']} - {job['max_salary']} "
            f"{job['salary_unit']}\n"
            f"🔗 {job['job_url']}"
        )

        response = requests.post(
            webhook_url,
            json={"content": message},
            timeout=10
        )

        response.raise_for_status()

    print(
        f"Sent {len(de_jobs)} new "
        f"Data Engineer jobs to Discord!"
    )