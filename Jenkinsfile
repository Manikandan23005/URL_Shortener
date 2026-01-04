pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'your-dockerhub-username/url-shortener'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
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
                    // Run a basic test: start the container and check if Flask app starts
                    dockerImage.inside('-p 5000:5000') {
                        sh '''
                            timeout 10 flask run --host=0.0.0.0 --port=5000 &
                            sleep 5
                            curl -f http://localhost:5000 || exit 1
                        '''
                    }
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'dockerhub-credentials') {
                        dockerImage.push("${DOCKER_TAG}")
                        dockerImage.push('latest')
                    }
                }
            }
        }
    }

    post {
        always {
            sh 'docker system prune -f'
        }
    }
}