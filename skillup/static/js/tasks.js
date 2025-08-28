import { API_BASE_URL } from "./config.js";

async function fetchTasks() {
  try {
    const res = await fetch(`${API_BASE_URL}/tasks/`, { credentials: "include" });
    if (!res.ok) return;
    const tasks = await res.json();
    displayTasks(tasks);
  } catch (e) {
    console.error(e);
  }
}

function card(html) { return `<div class="task-item">${html}</div>`; }

function displayTasks(tasks) {
  const assigned = document.getElementById("assigned-tasks");
  const ongoing = document.getElementById("ongoing-tasks");
  const done = document.getElementById("done-tasks");
  if (!assigned || !ongoing || !done) return;

  const assignedHTML = tasks.filter(t => t.status === "assigned")
    .map(t => card(`<h4>${t.title}</h4><a href="/task/detail/${t.id}" class="btn">View Task</a>`)).join("") || "<p>No assigned</p>";

  const ongoingHTML = tasks.filter(t => t.status === "ongoing" || t.status === "submitted")
    .map(t => card(`<h4>${t.title}</h4><a href="/task/detail/${t.id}" class="btn">Resume</a>`)).join("") || "<p>No ongoing</p>";

  const doneHTML = tasks.filter(t => t.status === "done" || t.status === "failed")
    .map(t => card(`<h4>${t.title}</h4><a href="/task/detail/${t.id}?review=true" class="btn">Review</a>`)).join("") || "<p>No done</p>";

  assigned.innerHTML = assignedHTML;
  ongoing.innerHTML = ongoingHTML;
  done.innerHTML = doneHTML;
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("assigned-tasks")) fetchTasks();
});
