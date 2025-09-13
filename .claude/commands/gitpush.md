`if [ -z "$1" ]; then
  echo "Usage: ./git_push.sh 'commit message'"
  exit 1
fi`


`git add .
git commit -m "$1"
git push origin main`
