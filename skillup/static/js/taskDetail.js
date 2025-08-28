import { getToken } from "./config.js";

document.addEventListener("DOMContentLoaded", function () {
  const container = document.getElementById("task-detail-container");
  if (!container) return;

  const taskId = container.dataset.taskId;
  const timeLimitMinutes = parseInt(container.dataset.timeLimit || "30", 10);

  const startBtn = document.getElementById("start-task-btn");
  const submitBtn = document.getElementById("submit-task-btn");
  const markdownDiv = document.getElementById("markdown-content");
  const countdownDiv = document.getElementById("countdown-timer");
  const timerValueSpan = document.getElementById("timer-value");

  let timeRemaining = timeLimitMinutes * 60;
  let countdownInterval = null;
  let taskOngoing = false;
  let submitted = false;

  async function postJSON(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: body ? JSON.stringify(body) : null,
    });
    return res;
  }

  async function submitTask(timeTaken) {
    try {
      const response = await postJSON(`/api/tasks/${taskId}/submit/`, { time_taken: timeTaken });
      if (response.ok) {
        submitted = true;
        alert("Task submitted successfully!");
        window.location.reload();
      } else {
        console.error("Failed to submit task", response.status);
      }
    } catch (error) {
      console.error("Error submitting task", error);
    }
  }

  async function failTask() {
    try {
      const response = await postJSON(`/api/tasks/${taskId}/fail/`, {});
      if (response.ok) {
        alert("Task marked as failed due to exit / timeout");
        window.location.reload();
      } else {
        console.error("Failed to mark task as failed", response.status);
      }
    } catch (error) {
      console.error("Error marking task as failed", error);
    }
  }

  if (startBtn) {
    startBtn.addEventListener("click", function () {
      if (markdownDiv) markdownDiv.style.display = "block";
      if (countdownDiv) countdownDiv.style.display = "block";

      startBtn.style.display = "none";
      if (submitBtn) submitBtn.style.display = "inline-block";
      taskOngoing = true;

      postJSON(`/api/tasks/${taskId}/start/`).catch(err => console.error("Failed to start task:", err));

      countdownInterval = setInterval(() => {
        if (timeRemaining <= 0) {
          clearInterval(countdownInterval);
          if (timerValueSpan) timerValueSpan.textContent = "Time is Up!!";
          failTask();
          taskOngoing = false;
          return;
        }
        timeRemaining--;
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        if (timerValueSpan) {
          timerValueSpan.textContent = `${minutes}m : ${seconds < 10 ? '0' + seconds : seconds}s`;
        }
      }, 1000);
    });
  }

  if (submitBtn) {
    submitBtn.addEventListener("click", function () {
      const totalTime = timeLimitMinutes * 60;
      const timeTaken = totalTime - timeRemaining;
      submitTask(timeTaken);
      clearInterval(countdownInterval);
      taskOngoing = false;
    });
  }

  window.addEventListener("beforeunload", function(event) {
    if (taskOngoing && !submitted) {
      event.returnValue = "You are about to exit and the task will be marked as failed";
    }
  });
});
