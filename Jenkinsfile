pipeline {
    environment {
        GITLAB = credentials("gitlab-jenkins")
        NEXUS = credentials("local-nexus")
    }
    parameters {
        string(defaultValue: "", description: 'Generate a release build with a tagged version', name: 'Release')
    }
    agent {
        docker {
            reuseNode true
            image 'ikus060/docker-debian-py2-py3:stretch'
            // Update host certificates chain.
            args '-v /etc/ssl/certs:/etc/ssl/certs:ro -v /usr/local/share/ca-certificates/pki:/usr/local/share/ca-certificates/pki:ro'
        }
    }
    stages {
        stage ('Setup') {
            steps {
                // Upgrade python and install dependencies to avoid compiling from sources.
                sh 'apt-get update && apt-get -qq install python-pysqlite2 libldap2-dev libsasl2-dev rdiff-backup node-less'
                sh 'pip install pip setuptools tox nose coverage --upgrade'
            }
        }
        stage ('Test') {
            steps {
                // Compile cataglog
                sh 'python setup.py build'
                sh "tox --recreate --workdir /tmp --sitepackages"
                
            }
            post {
                success {
                    junit "nosetests-*.xml"
                    step([$class: 'CoberturaPublisher', coberturaReportFile: "coverage-*.xml"])
                }
            }
        }
		stage ('Build') {
            steps {
                sh 'pip install wheel --upgrade'
                sh """cat > ~/.pypirc << EOF
[distutils]
index-servers =
  nexus

[nexus]
repository = https://nexus.patrikdufresne.com/repository/pypi/
username=${NEXUS_USR}
password=${NEXUS_PSW}   
EOF
"""
                sh 'python setup.py sdist bdist_wheel upload -r nexus'
            }
        }
        stage ('Release') {
            when {
                not { environment name: 'Release', value: '' }
            }
            steps {
                // Create Tag in git repo.
                sh """
                    git checkout .
                    git config --local user.email "jenkins@patrikdufresne.com"
                    git config --local user.name "Jenkins"
                    git tag 'v${Release}'
                    export REPO=`git config remote.origin.url`
                    git push http://${GITLAB}@\044{REPO#*//} --tags
                """
                addInfoBadge "v${Release}"
                // Build and upload
                sh 'python setup.py sdist bdist_wheel upload -r nexus'
            }
        }
    }
}
