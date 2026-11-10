<?php
session_start();

if (!isset($_SESSION['user_id'])) {
    header("Location: Login.html");
    exit();
}

include "config/database.php";

$user_id = $_SESSION['user_id'];

$sql = "SELECT * FROM users WHERE id = ?";
$stmt = mysqli_prepare($conn, $sql);
mysqli_stmt_bind_param($stmt, "i", $user_id);
mysqli_stmt_execute($stmt);

$result = mysqli_stmt_get_result($stmt);
$user = mysqli_fetch_assoc($result);
?>

<!DOCTYPE html>
<html>
<head>
    <title>AI Career Preparation System</title>

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f6f8;
        }

        header {
            background: #4f46e5;
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        header h2 {
            margin: 0;
        }

        .logout {
            background: white;
            color: #4f46e5;
            padding: 10px 18px;
            text-decoration: none;
            border-radius: 6px;
        }

        .container {
            width: 90%;
            max-width: 1100px;
            margin: 30px auto;
        }

        .welcome {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 25px;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }

        .card h3 {
            color: #4f46e5;
        }

        .btn {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 15px;
            background: #4f46e5;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }

        .ai-off {
            color: red;
            font-weight: bold;
        }

        .ai-on {
            color: green;
            font-weight: bold;
        }
    </style>
</head>

<body>

<header>
    <h2>AI Career Preparation System</h2>

    <a class="logout" href="logout.php">Logout</a>
</header>

<div class="container">

    <div class="welcome">
        <h2>Welcome, <?php echo htmlspecialchars($user['name']); ?> 👋</h2>

        <p>
            Career Goal:
            <strong>
                <?php echo htmlspecialchars($user['career_goal']); ?>
            </strong>
        </p>
    </div>

    <div class="cards">

        <div class="card">
            <h3>📝 Career Assessment</h3>
            <p>Take an assessment to understand your technical skills.</p>
            <a href="exam/start_exam.php" class="btn">Start Exam</a>
        </div>

        <div class="card">
            <h3>🤖 AI Career Assistant</h3>
            <p>Get personalized career guidance from AI.</p>
            <p class="ai-on">AI MODE: ON</p>
            <a href="ai/ai_chat.php" class="btn">Open AI</a>
        </div>

        <div class="card">
            <h3>📄 Resume Analyzer</h3>
            <p>Upload your resume and receive improvement suggestions.</p>
            <a href="resume/upload_resume.php" class="btn">Analyze Resume</a>
        </div>

        <div class="card">
            <h3>🎤 Interview Preparation</h3>
            <p>Practice technical and HR interview questions.</p>
            <a href="interview/interview.php" class="btn">Start Interview</a>
        </div>

    </div>

</div>

</body>
</html>