export const API_BASE_URL = "/api";
export function getToken() {
  return localStorage.getItem("access_token") || "";
}
