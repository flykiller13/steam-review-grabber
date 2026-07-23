pipeline {
    agent any

    triggers {
        cron('H */6 * * *')
    }

    environment {
        DISCORD_WEBHOOK_URL = credentials('discord-reviews-webhook')
        // Comma-separated "appid=Game Name" pairs, e.g. "123456=My Game,234567=Other Game"
        STEAM_APPID = credentials('steam-games')
        STEAM_REVIEWS_STATE_DIR = 'C:\\Jenkins\\data\\steam_reviews'
    }

    stages {
        stage('Setup') {
            steps {
                bat 'python -m pip install --quiet requests'
            }
        }
        stage('Fetch & post reviews') {
            steps {
                bat 'python steam_reviews.py'
            }
        }
    }
}
