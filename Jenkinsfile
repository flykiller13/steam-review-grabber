pipeline {
    agent any

    triggers {
        cron('H */6 * * *')
    }

    parameters {
        booleanParam(name: 'CAT_CHESS', defaultValue: true, description: 'Cat Chess (4163030)')
        booleanParam(name: 'EOM',       defaultValue: true, description: 'EOM (4129510)')
        booleanParam(name: 'LOTS',      defaultValue: true, description: 'LotS (2848220)')
        booleanParam(name: 'SOR',       defaultValue: true, description: 'SoR (1380070)')
        booleanParam(name: 'OH',        defaultValue: true, description: 'OH (2553420)')
    }

    environment {
        DISCORD_WEBHOOK_URL = credentials('discord-reviews-webhook')
        STEAM_REVIEWS_STATE_DIR = 'C:\\Jenkins\\data\\steam_reviews'
    }

    stages {
        stage('Setup') {
            steps {
                bat 'python -m pip install requests'
            }
        }
        stage('Fetch & post reviews') {
            steps {
                script {
                    def games = [
                        CAT_CHESS: ['4163030', 'Cat Chess'],
                        EOM:       ['4129510', 'EOM'],
                        LOTS:      ['2848220', 'LotS'],
                        SOR:       ['1380070', 'SoR'],
                        OH:        ['2553420', 'OH'],
                    ]
                    def args = games
                        .findAll { key, game -> params[key] }
                        .collect { key, game -> "\"${game[0]}=${game[1]}\"" }
                        .join(' ')
                    if (args) {
                        bat "python steam_reviews.py ${args}"
                    } else {
                        echo 'No games selected, nothing to do'
                    }
                }
            }
        }
    }
}
