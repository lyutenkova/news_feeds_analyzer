# news_feeds_analyzer
Analysis of popular news feeds.
As a result of the script will be generate an html-report (./report.html) that contains following information:
    1. Top-5 mentioned news in the news feeds with the links to the primary source piece of news; 
    2. List of unique news for every news feed with links to news;
    3. Quantity of news in every news feed.
    
Which sources should be used is defined in the file ./conf.json.
To start the application you need to clone the repository and enter a command pip install -r ./requirements.txt
at the command line to install the necessary libraries. After installing the libraries, run the application with the command python3 news_feeds_analyzer.py and wait for the creation of an html report with the result ./report.html.
