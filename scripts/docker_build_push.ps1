param(
    [Parameter(Mandatory=$true)][string]$RepoTag
)

if ($RepoTag -notmatch ':') { $RepoTag = "$RepoTag`:latest" }

Write-Host "Building image $RepoTag"
docker build -t $RepoTag .

Write-Host "Pushing image $RepoTag"
docker push $RepoTag

Write-Host "Done."
