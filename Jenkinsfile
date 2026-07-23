pipeline {
    agent any

    triggers {
        cron('H */6 * * *')
    }

    environment {
        DISCORD_WEBHOOK_URL = credentials('discord-reviews-webhook')
        // Secret-file credential holding games.json (see README for the format)
        STEAM_GAMES_FILE = credentials('steam-games-file')
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
