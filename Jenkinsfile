pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "manikandan791/url-shortener"
        DOCKER_TAG   = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    dockerImage.inside {
                        sh '''
                          sleep 3
                          curl -f http://localhost:5000 || exit 1
                        '''
                    }
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'dockerhub-creds') {
                        dockerImage.push("${DOCKER_TAG}")
                        dockerImage.push('latest')
                    }
                }
            }
        }
    }

    post {
        always {
            sh 'docker system prune -f || true'
        }
    }
}
