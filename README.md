---

# 📰 Personalized News Aggregator

A Django-based application that fetches news from multiple sources, generates AI summaries, performs simple bias detection, and displays personalized content on a clean dashboard.

This project is **completed up to the current planned phase**, and additional improvements are planned for future versions.

---

## ✨ Features Completed So Far

* Fetches articles from APIs and RSS feeds
* AI-based summarization (using Transformers)
* Basic keyword-based bias detection
* User authentication and dashboard
* Celery + Redis for background tasks
* Caching and improved performance
* Category and search filtering
* Clean UI with pagination

---

## 🚀 Future Improvements (Planned)

* More accurate ML-based bias classifier
* Better personalization / recommendation engine
* UI/UX improvements
* Performance optimization
* Additional news sources
* Deployment setup and environment configs

---

## 🏗️ Setup Instructions

### Clone the repository

```
git clone https://github.com/<your-username>/personalized-news-aggregator.git
cd personalized-news-aggregator
```

### Install dependencies

```
pip install -r requirements.txt
```

### Run migrations

```
python manage.py migrate
```

### Start Redis

```
redis-server
```

### Start Celery workers

```
celery -A config worker -l info -Q high,medium,low
celery -A config beat -l info
```

### Start Django server

```
python manage.py runserver
```

---

## 🤝 Contributing

If you wish to improve or extend the project, feel free to open issues or submit pull requests.
Suggestions and enhancements are always appreciated.

---

## 📄 License

This project is released under the **MIT License**, allowing others to use and modify the code with attribution.

---
