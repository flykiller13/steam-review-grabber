pipeline {

    triggers {
        cron('H */6 * * *')
    }

    environment {
        DISCORD_WEBHOOK_URL = credentials('discord-reviews-webhook')
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
                bat 'python steam_reviews.py 123456'
                // bat 'python steam_reviews.py 789012'  // add more games here
            }
        }
    }
}