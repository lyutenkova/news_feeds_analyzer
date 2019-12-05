import os
import datetime
import feedparser
import difflib
import json


class Feed:
    def __init__(self, title, link, articles):
        self.title = title
        self.link = link
        self.articles = articles
        self.amount_articles = len(articles)


class Article:
    def __init__(self, title, pub_date, link):
        self.title = title
        self.pub_date = pub_date
        self.link = link
        self.is_unique = True


def read_json(file_path):
    json_data = {}

    if not os.path.exists(file_path):
        raise Exception("File not found")

    with open(file_path, "r") as f:
        json_data = json.load(f)

    return json_data["links"]


def parse_newsfeed(link):
    return feedparser.parse(link)


def create_html_report(most_mentioned_art, feeds):
    f = open('report.html','w')

    table_rows = "<tr><th>Number</th><th>Primary</th><th>Similar</th></tr>"
    row = "<tr><td>{idx}</td><td><a href={primary}>{primary_title}</a></td><td><ol>{articles}</ol></td></tr>"
    
    for index, cluster in enumerate(most_mentioned_art):
        table_rows += row.format(
            idx=index+1,
            primary=str(cluster[0].link),
            primary_title=cluster[0].title,
            articles="\n".join("<li><a href={art}>{art_title}</a></li>".format(art=str(art.link), art_title=art.title) for art in cluster[1:])
        )

    table_feed = "<tr><th>Feed</th><th>Amount</th><th>Unique articles</th></tr>"
    feed_row = "<tr><td><a href={feed_link}>{feed_title}</a></td><td>{amount}</td><td><ol>{unique_articles}</ol></td></tr>"

    for feed in feeds:
        table_feed += feed_row.format(
            feed_link=feed.link,
            feed_title=feed.title,
            amount = feed.amount_articles,
            unique_articles="\n".join("<li><a href={art}>{art_title}</a></li>".format(art=str(art.link), art_title=art.title) for art in feed.articles if art.is_unique)
        )

    report = """<html>
    <head>
    <link rel="stylesheet" href="./style.css">
    </head>
    <body>
    <table class="table">
    <caption>Top 5 mentioned</caption>
        {table}
    </table>
    <br/>
    <br/>
    <table class="table">
    <caption>Feeds</caption>
        {table2}
    </table>
    </body>
    </html>""".format(table=table_rows, table2=table_feed)

    f.write(report)
    f.close()


def build_adjacency_matrix(news_titles):
    import numpy as np
    adj_matrix = np.zeros((len(news_titles), len(news_titles)))

    for i in range(len(news_titles)):
        for j in range(i + 1, len(news_titles)):
            adj_matrix[i, j] = adj_matrix[j, i] = similarity(news_titles[i], news_titles[j])

    return adj_matrix


def null_row_col(matrix, idx):
    for j in range(len(matrix[idx])):
        matrix[idx, j] = matrix[j, idx] = 0


def get_clusters(matrix):
    repeated_clusters, unique_articles = [], []

    THRESHOLD = 0.55

    for i in range(len(matrix)):
        if i not in unique_articles and all([i not in c for c in repeated_clusters]):
            cluster = set([i])

            for j in range(i+1, len(matrix)):
                if matrix[i, j] > THRESHOLD:
                    cluster.add(j)
                    null_row_col(matrix, j)

            if len(cluster) == 1:
                unique_articles.append(list(cluster)[0])
            else:
                repeated_clusters.append(cluster)

            null_row_col(matrix, i)

    return repeated_clusters, unique_articles


def similarity(article_1, article_2):
    normalized1 = article_1.lower()
    normalized2 = article_2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()


def _get_feed(newsfeed):
    articles = []
    data = parse_newsfeed(newsfeed["link"])  # парсим каждую новостную ленту

    for article in data.entries:
        articles.append(
            Article(
                article.title,
                getattr(article, "published_parsed", datetime.datetime.now().timetuple()),
                article.link
            )
        )

    return Feed(newsfeed["title"], newsfeed["link"], articles)


def get_feeds(newsfeeds):
    return [_get_feed(newsfeed) for newsfeed in newsfeeds]


def sort_by_mentions(clusters_list):
    clusters_list.sort(key=lambda l: len(l), reverse=True)


if __name__ == "__main__":
    # все новостные ленты из конфига (названия - ссылки)
    newsfeeds = read_json("./config.json")
    feeds = get_feeds(newsfeeds)

    title_idx_to_feed_idx = {}
    titles = []

    for feed_idx, f in enumerate(feeds):
        for art_idx, art in enumerate(f.articles):
            titles.append(art.title)
            # ссответсвие индекса в массиве titles индексу в feed
            title_idx_to_feed_idx[len(titles)-1] = (feed_idx, art_idx)

    matrix = build_adjacency_matrix(titles)  # матрица смежности

    most_mentioned_clusters, unique_articles = get_clusters(matrix)

    sort_by_mentions(most_mentioned_clusters)  # отсортируем по кол-ву новостей в кластере
    most_mentioned = []  # все данные по наиболее упомянутым новостям в порядке публикации (первая новость в кластере - первоисточник)

    for cl in most_mentioned_clusters:
        cluster = []
        for title_idx in cl:
            feed_idx, art_idx = title_idx_to_feed_idx[title_idx]
            article = feeds[feed_idx].articles[art_idx]
            article.is_unique = False
            cluster.append(article)

            cluster.sort(key=lambda item: item.pub_date, reverse=True)

        most_mentioned.append(cluster)

    # for title_idx in unique_articles:
    #     feed_idx, art_idx = title_idx_to_feed_idx[title_idx]
    #     article = feeds[feed_idx].articles[art_idx] 
    #     print(article.feed_idx)

    create_html_report(most_mentioned[:5], feeds)