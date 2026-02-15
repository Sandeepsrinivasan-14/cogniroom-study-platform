$ErrorActionPreference = 'Stop'

Write-Host 'Phase 5B test: quiz attempts + events' -ForegroundColor Cyan

# 1) Login SocketUser
$loginBody = @{
    name     = 'SocketUser'
    email    = 'socket@test.com'
    password = 'pass123'
    role     = 'student'
} | ConvertTo-Json

$login   = Invoke-RestMethod -Uri 'http://localhost:8000/auth/login' -Method Post -Body $loginBody -ContentType 'application/json' -TimeoutSec 10
$token   = $login.access_token
$headers = @{ Authorization = "Bearer $token" }

# 2) Pick a room where SocketUser is a member (use first from /rooms/my)
$myRooms = Invoke-RestMethod -Uri 'http://localhost:8000/rooms/my' -Method Get -Headers $headers -TimeoutSec 10
if (-not $myRooms.rooms -or $myRooms.rooms.Count -eq 0) {
    throw "SocketUser has no rooms to use for quiz test."
}
$roomId = $myRooms.rooms[0].id
Write-Host ("Using room id={0}" -f $roomId) -ForegroundColor Yellow

# 3) Create a quiz in that room
$quizBody = @{
    title = 'Attempt Test Quiz'
    questions = @(
        @{ text = 'what is 2 + 2?' },
        @{ text = 'hello?' }
    )
} | ConvertTo-Json

$quiz = Invoke-RestMethod -Uri ("http://localhost:8000/rooms/{0}/quizzes" -f $roomId) -Method Post -Body $quizBody -ContentType 'application/json' -Headers $headers -TimeoutSec 10
Write-Host ("Created quiz id={0} title={1}" -f $quiz.id, $quiz.title) -ForegroundColor Green

# 4) Submit an attempt: 1 correct (matching text exactly), 1 wrong
$answers = @(
    @{ question_id = $quiz.questions[0].id; answer = 'what is 2 + 2?' },  # correct by simple rule
    @{ question_id = $quiz.questions[1].id; answer = 'wrong answer' }     # incorrect
)
$attemptBody = @{ answers = $answers } | ConvertTo-Json

$attempt = Invoke-RestMethod -Uri ("http://localhost:8000/quizzes/{0}/attempts" -f $quiz.id) -Method Post -Body $attemptBody -ContentType 'application/json' -Headers $headers -TimeoutSec 10
Write-Host ("Attempt id={0} score={1}/{2}" -f $attempt.id, $attempt.score, $attempt.total_questions) -ForegroundColor Green

# 5) Fetch events for this room to see quiz_started / question_answered / quiz_finished
$events = Invoke-RestMethod -Uri ("http://localhost:8000/rooms/{0}/events" -f $roomId) -Method Get -Headers $headers -TimeoutSec 10
Write-Host ("Events for room {0} (latest first):" -f $roomId) -ForegroundColor Magenta

$events.events | Select-Object -First 10 | ForEach-Object {
    Write-Host ("[{0}] type={1} payload={2}" -f $_.created_at, $_.type, $_.payload) -ForegroundColor Yellow
}
