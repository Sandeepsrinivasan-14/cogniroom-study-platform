$ErrorActionPreference = 'Stop'

Write-Host 'Phase 4 test: event logging' -ForegroundColor Cyan

# 1) Login existing SocketUser
$loginBody = @{
    name     = 'SocketUser'
    email    = 'socket@test.com'
    password = 'pass123'
    role     = 'student'
} | ConvertTo-Json

$login = Invoke-RestMethod -Uri 'http://localhost:8000/auth/login' -Method Post -Body $loginBody -ContentType 'application/json' -TimeoutSec 10
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }

# 2) Create room
$roomBody = @{ name = 'EventLog Room' } | ConvertTo-Json
$room = Invoke-RestMethod -Uri 'http://localhost:8000/rooms' -Method Post -Body $roomBody -ContentType 'application/json' -Headers $headers -TimeoutSec 10
Write-Host ('Created room id={0}, code={1}' -f $room.id, $room.code) -ForegroundColor Green

# 3) Join same room (no-op but logs room_joined)
$joined = Invoke-RestMethod -Uri ("http://localhost:8000/rooms/join/{0}" -f $room.code) -Method Post -Headers $headers -TimeoutSec 10
Write-Host ('Joined room id={0}' -f $joined.id) -ForegroundColor Green

# 4) Fetch events for this room
$events = Invoke-RestMethod -Uri ("http://localhost:8000/rooms/{0}/events" -f $room.id) -Method Get -Headers $headers -TimeoutSec 10
Write-Host ('Events for room {0}:' -f $room.id) -ForegroundColor Magenta

$events.events | ForEach-Object {
    Write-Host ("[{0}] type={1} user_id={2} payload={3}" -f $_.created_at, $_.type, $_.user_id, $_.payload) -ForegroundColor Yellow
}
