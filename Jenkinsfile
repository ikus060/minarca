pipeline {
    environment {
        GITLAB = credentials("gitlab-jenkins")
    }
    parameters {
        booleanParam(defaultValue: false, description: 'Generate a release build with a tagged version.', name: 'Release')
        booleanParam(defaultValue: false, description: 'Promote build for production.', name: 'Promote')
    }
    agent {
        node {
          label 'docker'
        }
    }
    stages {
        stage ('Parallel Test') {
            steps {
                script {
                    def axisImages = ['jessie', 'stretch']
                    def axisPython = ['py27', 'py3']
                    def axisCherrypy = ['cherrypy14']
                    //def axisCherrypy = ['cherrypy35','cherrypy4','cherrypy5','cherrypy6','cherrypy7','cherrypy8','cherrypy9','cherrypy10','cherrypy11','cherrypy12','cherrypy13','cherrypy14']
                    
                    def builders = [:]
                    for (x in axisImages) {
                    for (y in axisPython) {
                    for (z in axisCherrypy) {
                        // Need to bind the label variable before the closure - can't do 'for (label in labels)'
                        def image = x 
                        def python = y
                        def cherrypy = z
                        def env = "${python}-${cherrypy}"
                    
                        // Create a map to pass in to the 'parallel' step so we can fire all the builds at once
                        builders["Test ${image}-${env}"] = {
                            node('docker') {
                                /* Requires the Docker Pipeline plugin to be installed */
                                docker.image("ikus060/docker-debian-py2-py3:${image}").inside {
                                    // Wipe working directory to make sure to build clean.
                                    deleteDir() 
                                    checkout scm
                                    
                                    // Upgrade python and install dependencies to avoid compiling from sources.
                                    sh 'apt-get update && apt-get -qq install python-pysqlite2 libldap2-dev libsasl2-dev rdiff-backup node-less'
                                    sh 'pip install pip setuptools tox --upgrade'
                                
                                    // Compile cataglog
                                    sh 'python setup.py build'
                                    
                                    // Run test
                                    try {
                                        sh "tox --recreate --workdir /tmp --sitepackages -e ${env}"
                                    } finally {
                                        junit "nosetests-${env}.xml"
                                        stash includes: "coverage-${env}.xml", name: 'coverage'
                                    }
                                }
                            }
                        }
                    }}}
                    parallel builders
                }
            }
        }
        stage ('Publish Coverage') {
            steps {
                unstash 'coverage'
                script {
                    step([$class: 'CoberturaPublisher', coberturaReportFile: "coverage-*.xml"])
                }
            }
        }
		stage ('Build') {
            agent {
                docker {
                    reuseNode true
                    image 'ikus060/docker-debian-py2-py3:jessie'
                }
            }
            steps {
				sh 'pip install wheel --upgrade'
                sh 'python setup.py sdist bdist_wheel'
            }
        }
        stage ('Release') {
            when {
                environment name: 'Release', value: 'true'
            }
            agent {
                docker {
                    reuseNode true
                    image 'ikus060/docker-debian-py2-py3:jessie'
                }
            }
            steps {
                script {
                    version = sh(
                        script: 'python setup.py --version | tail -n1',
                        returnStdout: true
                    ).trim()
                    version = version.replaceFirst(".dev.*", "+${BUILD_NUMBER}")
                }
                sh 'git checkout .'
                // Change version.
                sh """
                    sed -i.bak -r "s/version='(.*).dev.*'/version='${version}'/" setup.py
                """
                // Create Tag in git repo.
                sh """
                    git config --local user.email "jenkins@patrikdufresne.com"
                    git config --local user.name "Jenkins"
                    git tag 'v${version}'
                    export REPO=`git config remote.origin.url`
                    git push http://${GITLAB}@\044{REPO#*//} --tags
                """
                addInfoBadge "v${version}"
            }
        }
        stage('Promote') {
            when {
                environment name: 'Release', value: 'true'
                environment name: 'Promote', value: 'true'
                branch 'master'
            }
            agent {
                docker {
                    reuseNode true
                    image 'ikus060/docker-debian-py2-py3:jessie'
                }
            }
            steps {
                sh """cat > ~/.pypirc << EOF
[distutils]
index-servers =
  pypi

[pypi]
username=${PYPI_USR}
password=${PYPI_PSW}   
EOF
"""
                sh 'pip install wheel --upgrade'
                sh 'python setup.py sdist bdist_wheel upload -r pypi'
            }
        }
        stage('GitHubPush') {
            steps { 
                sh "git push --force https://${GITHUB}@github.com/ikus060/rdiffweb.git refs/remotes/origin/${BRANCH_NAME}:refs/heads/${BRANCH_NAME}"
                sh "git push https://${GITHUB}@github.com/ikus060/rdiffweb.git --tags"
            }
        }
    }
}
