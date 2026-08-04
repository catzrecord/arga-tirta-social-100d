param(
  [string]$Repository = "catzrecord/arga-tirta-social-100d",
  [string]$GraphVersion = "v25.0"
)

$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
if (-not (Test-Path -LiteralPath $gh)) { $gh = "gh" }

$accountId = (Read-Host "Instagram User ID Arga Tirta").Trim()
$secureToken = Read-Host "Meta Instagram access token" -AsSecureString
$tokenPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
try {
  $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPtr)
  $uri = "https://graph.instagram.com/$GraphVersion/$accountId?fields=id,username,account_type&access_token=$([uri]::EscapeDataString($token))"
  $account = Invoke-RestMethod -Uri $uri -Method Get
  if ([string]$account.id -ne $accountId) { throw "Token mengarah ke Instagram User ID yang berbeda." }

  $token | & $gh secret set META_ACCESS_TOKEN --repo $Repository
  $accountId | & $gh secret set INSTAGRAM_USER_ID --repo $Repository
  & $gh variable set EXPECTED_INSTAGRAM_USERNAME --body ([string]$account.username) --repo $Repository
  & $gh workflow run arga-tirta-instagram.yml --repo $Repository --ref main -f mode=verify

  Write-Host "Meta account terverifikasi: @$($account.username) [$($account.account_type)]" -ForegroundColor Green
  Write-Host "GitHub Actions verify sudah dijalankan." -ForegroundColor Green
}
finally {
  if ($tokenPtr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPtr) }
  $token = $null
}
