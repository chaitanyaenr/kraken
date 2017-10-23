#!/bin/bash

gopath=$1
function help(){
	echo "Usage: setup-env.sh <gopath>"
}
if [[ $gopath == "" ]]; then
	gopath="/root/.go"
fi
# Install go, dependencies
pip install -r requirements.txt
which go &>/dev/null
if [[ $? != 0 ]]; then
	yum -y install go &>/dev/null
fi
if [[ $(echo $GOPATH) == "" ]];then
	mkdir -p $gopath_dir/.go
	echo "GOPATH=$gopath_dir/.go" >> ~/.bashrc
	echo "export GOPATH" >> ~/.bashrc
	echo "PATH=\$PATH:\$GOPATH/bin # Add GOPATH/bin to PATH for scripting" >> ~/.bashrc
	source ~/.bashrc
fi
# get kube-monkey
go get github.com/asobti/kube-monkey
cd $GOPATH/src/github.com/asobti/kube-monkey
make container
