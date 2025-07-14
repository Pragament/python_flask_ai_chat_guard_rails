document.getElementById("addRule").addEventListener("click", () => {
  const urlPattern = document.getElementById("urlPattern").value.trim();
  const cssSelector = document.getElementById("cssSelector").value.trim();

  if (!urlPattern || !cssSelector) {
    alert("Please enter both fields.");
    return;
  }

  chrome.storage.sync.get(["rules"], (data) => {
    const rules = data.rules || [];

    rules.push({ pattern: urlPattern, selector: cssSelector });

    chrome.storage.sync.set({ rules }, () => {
      alert("✅ Rule added!");
      displayRules(rules);
      document.getElementById("urlPattern").value = "";
      document.getElementById("cssSelector").value = "";
    });
  });
});

function displayRules(rules) {
  const ruleList = document.getElementById("ruleList");
  ruleList.innerHTML = "";
  rules.forEach((rule, i) => {
    const li = document.createElement("li");
    li.textContent = `Pattern: ${rule.pattern}, Selector: ${rule.selector}`;
    ruleList.appendChild(li);
  });
}

// Load rules on popup open
chrome.storage.sync.get(["rules"], (data) => {
  displayRules(data.rules || []);
});
