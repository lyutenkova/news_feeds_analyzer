import os
import argparse
import datetime
import difflib
import json

import feedparser


THRESHOLD = 0.55


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
    with open('report.html','w') as f:
        table_rows = "<tr><th>Number</th><th>Primary</th><th>Similar</th></tr>"
        row_tmpl = "<tr><td>{idx}</td><td><a href={primary}>{primary_title}</a></td><td><ol>{articles}</ol></td></tr>"
        
        for index, cluster in enumerate(most_mentioned_art, start=1):
            table_rows += row_tmpl.format(
                idx=index,
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
            {table_row}
        </table>
        <br/>
        <br/>
        <table class="table">
        <caption>Feeds</caption>
            {table_feed}
        </table>
        </body>
        </html>""".format(table_row=table_rows, table_feed=table_feed)

        f.write(report)


def build_adjacency_matrix(news_titles):
    adj_matrix = [[0 for i in range(len(news_titles))] for i in range(len(news_titles))]

    for i in range(len(news_titles)):
        for j in range(i + 1, len(news_titles)):
            adj_matrix[i][j] = adj_matrix[j][i] = similarity(news_titles[i], news_titles[j])

    return adj_matrix


def null_row_col(matrix, idx):
    for j in range(len(matrix[idx])):
        matrix[idx][j] = matrix[j][idx] = 0


def get_clusters(matrix):
    repeated_clusters = []

    for i in range(len(matrix)):
        if all([i not in c for c in repeated_clusters]):
            cluster = set([i])

            for j in range(i+1, len(matrix)):
                if matrix[i][j] > THRESHOLD:
                    cluster.add(j)
                    null_row_col(matrix, j)

            if len(cluster) != 1:
                repeated_clusters.append(cluster)

            null_row_col(matrix, i)

    return repeated_clusters


def similarity(article_1, article_2):
    normalized1 = article_1.lower()
    normalized2 = article_2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()


def get_feed(newsfeed):
    articles = []
    data = parse_newsfeed(newsfeed["link"])  # parse each newsfeed

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
    return [get_feed(newsfeed) for newsfeed in newsfeeds]


def sort_by_mentions(clusters_list):
    clusters_list.sort(key=lambda l: len(l), reverse=True)


if __name__ == "__main__":
    # all newsfeeds from config file (titles - links)
    newsfeeds = read_json("./config.json")
    feeds = get_feeds(newsfeeds)

    title_idx_to_feed_idx = {}
    titles = []

    for feed_idx, f in enumerate(feeds):
        for art_idx, art in enumerate(f.articles):
            titles.append(art.title)
            # compliance of the index in the array of titles and index of feed
            title_idx_to_feed_idx[len(titles)-1] = (feed_idx, art_idx)

    matrix = build_adjacency_matrix(titles)  # adjacency matrix for all articles by titles

    most_mentioned_clusters = get_clusters(matrix)

    sort_by_mentions(most_mentioned_clusters)  # sort by amount of articles in cluster
    most_mentioned = []  # first article - primary source

    for cl in most_mentioned_clusters:
        cluster = []
        for title_idx in cl:
            feed_idx, art_idx = title_idx_to_feed_idx[title_idx]
            article = feeds[feed_idx].articles[art_idx]
            article.is_unique = False
            cluster.append(article)

            cluster.sort(key=lambda item: item.pub_date, reverse=True)

        most_mentioned.append(cluster)

    create_html_report(most_mentioned[:5], feeds)