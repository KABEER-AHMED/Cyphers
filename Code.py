import sys
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QFrame, QLineEdit, QMainWindow, QPushButton, QScrollArea, QWidget, QGridLayout, QLabel
import praw
import webbrowser
import requests
import instaloader
from googleapiclient.discovery import build
from pytube import YouTube
import isodate


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyphers Application")
        self.max_results = 30
        self.initUI()
        self.apistuff()

    # General UI
    def initUI(self):
        self.setFixedSize(700, 480)  # size of window

        self.gui_layout = QGridLayout()

        self.label = QLabel("Cyphers Application")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 20px")

        self.entry = QLineEdit()
        self.entry.returnPressed.connect(self.searchVid)

        self.button = QPushButton("Search")
        self.button.clicked.connect(self.searchVid)

        self.frame = QFrame()
        self.frame.setStyleSheet("background-color: gray; border: 5px; border-radius: 10")
        self.frame_layout = QGridLayout()
        self.frame_layout.setSpacing(10)
        self.frame.setLayout(self.frame_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.frame)

        self.gui_layout.addWidget(self.label, 0, 0, 1, 2)
        self.gui_layout.addWidget(self.entry, 1, 0)
        self.gui_layout.addWidget(self.button, 1, 1)
        self.gui_layout.addWidget(self.scroll_area, 2, 0, 1, 2)

        self.widget = QWidget()
        self.widget.setLayout(self.gui_layout)
        self.setCentralWidget(self.widget)

    # Searching video
    def searchVid(self):
        keyword = self.entry.text()

        try:
            # Data of videos
            self.videos = []

            # Youtube
            request = self.youtube.search().list(
                part="snippet",
                q=keyword,
                maxResults=self.max_results,
                type="video"
            )
            self.youtube_results = request.execute()
            for item in self.youtube_results['items']:
                duration = item['contentDetails']['duration']
                duration_seconds = isodate.parse_duration(duration).total_seconds()

                if duration_seconds < 60:
                    continue  # Skip YouTube Shorts (less than 60 seconds)

                video_id = item['id']['videoId']
                thumbnail_url = item['snippet']['thumbnails']['default']['url']
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                yt = YouTube(video_url)
                video_stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
                video_mp4_link = video_stream.url

                self.videos.append({'type': "youtube", 'url': video_mp4_link, 'thumbnail': thumbnail_url})

            # Instagram
            count = 0
            for post in instaloader.Profile.from_username(self.instagram.context, "cats_of_instagram").get_posts():  # type: ignore
                if post.is_video:
                    self.videos.append({'type': "instagram", 'url': post.video_url, 'thumbnail': post.url})

                count += 1
                if count == self.max_results: break

            # Instagram Testing
            # insta_usr = 'hackaton'
            # insta_pass = 'budumtsss'
            # try:
            #     self.instagram.login(insta_usr, insta_pass)
            # except Exception as e:
            #     print(f"Login failed: {e}")
            # insta_profiles = instaloader.TopSearchResults(self.instagram.context, keyword)
            # insta_acc = next(insta_profiles.get_profiles(), None)
            # insta_profile = instaloader.Profile.from_username(self.instagram.context, insta_acc.username)
            #
            # count = 0
            # for post in insta_profile.get_posts():  # type: ignore
            #     if post.is_video:
            #         caption = post.caption
            #         if keyword.lower() in caption.lower():
            #             self.videos.append({'type': "instagram", 'url': post.video_url, 'thumbnail': post.url})
            #
            #     count += 1
            #     if count == self.max_results: break

            # Reddit
            subreddit_name = "cats"
            subreddit = self.reddit.subreddit(subreddit_name)
            search_results = subreddit.search(keyword, sort="hot", limit=self.max_results)  # limit is maximum amount of videos
            for submission in search_results:
                if submission.is_video:
                    url = submission.media['reddit_video']['fallback_url']
                    self.videos.append({'type': 'reddit', 'url': url, 'thumbnail': submission.thumbnail})

        except:
            pass

        print(self.videos)
        # Clear results before new ones
        for i in reversed(range(self.frame_layout.count())): 
            self.frame_layout.itemAt(i).widget().setParent(None)  # type: ignore


        # UI
        row = [0, 0, 1] 
        column = [0, 2, 0]
        index = 0
        for video in self.videos:
            if video['type'] == "youtube":
                self.image_label = CustomLabel(self.frame, index)
                self.image_label.setFixedSize(210, 100)
                pixmap = QPixmap()
                request = requests.get(video['thumbnail'])
                pixmap.loadFromData(request.content)
                pixmap = pixmap.scaled(QSize(210, 100))
                self.image_label.setPixmap(pixmap)
                self.frame_layout.addWidget(self.image_label, row[0], column[0], 1, 2)

                self.image_label.clicked.connect(lambda meta=index: self.open_video(meta))

                if column[0] == 3: row[0] += 2; column[0] = 0
                else: column[0] += 3

            elif video['type'] == "instagram":
                self.image_label = CustomLabel(self.frame, index)
                self.image_label.setFixedSize(100, 210)
                pixmap = QPixmap()
                request = requests.get(video['thumbnail'])
                pixmap.loadFromData(request.content)
                pixmap = pixmap.scaled(QSize(100, 210))
                self.image_label.setPixmap(pixmap)
                self.frame_layout.addWidget(self.image_label, row[1], column[1], 2, 1)

                self.image_label.clicked.connect(lambda meta=index: self.open_video(meta))

                if column[1] == 5: row[1] += 2; column[1] = 2
                else: column[1] += 3

            elif video['type'] == "reddit":
                self.image_label = CustomLabel(self.frame, index)
                self.image_label.setFixedSize(100, 100)
                pixmap = QPixmap()
                request = requests.get(video['thumbnail'])
                pixmap.loadFromData(request.content)
                pixmap = pixmap.scaled(QSize(100, 100))
                self.image_label.setPixmap(pixmap)
                self.frame_layout.addWidget(self.image_label, row[2], column[2])

                self.image_label.clicked.connect(lambda meta=index: self.open_video(meta))

                if column[2] == 1: column[2] += 2
                elif column[2] == 4: row[2] += 2; column[2] = 0
                else: column[2] += 1

            index += 1


    # API
    def apistuff(self):
        # Reddit
        reddit_client_id = "YIRjXpCltAxP8sTuLLMR8A"
        reddit_client_secret = "bKtAYHfPrxeoWlZHQCmgxXwB0JCrDQ"
        user_agent = "Hackathon"

        self.reddit = praw.Reddit(
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            user_agent=user_agent
        )

        # Youtube
        self.youtube_api_key = "AIzaSyBxJbw40GZhWTH0BQveCRPKFB1jSZdoqLg"
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)

        # Instagram
        self.instagram = instaloader.Instaloader()  # type: ignore


    # Opening selected video in browser
    def open_video(self, index):
        webbrowser.open(self.videos[index]["url"])


# Custom label to make it clickable
class CustomLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent, index):
        super().__init__(parent)
        self.index = index

    def mousePressEvent(self, event):  # type: ignore
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())
