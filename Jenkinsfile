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
                sh '''
                  docker build -t $DOCKER_IMAGE:$DOCKER_TAG .
                  docker tag $DOCKER_IMAGE:$DOCKER_TAG $DOCKER_IMAGE:latest
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                  docker run -d -p 5000:5000 --name test_container $DOCKER_IMAGE:$DOCKER_TAG
                  sleep 5
                  curl -f http://localhost:5000
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([string(credentialsId: 'dockerhub-token', variable: 'DOCKER_TOKEN')]) {
                    sh '''
                      echo $DOCKER_TOKEN | docker login -u manikandan791 --password-stdin
                      docker push $DOCKER_IMAGE:$DOCKER_TAG
                      docker push $DOCKER_IMAGE:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            sh '''
              docker rm -f test_container || true
              docker system prune -f || true
            '''
        }
    }
}
