// ===== CareerForge AI – Main Script =====

document.addEventListener("DOMContentLoaded", () => {
    // ---------- DOM references ----------
    const uploadArea = document.getElementById("upload-area");
    const resumeInput = document.getElementById("resume-input");
    const filePreview = document.getElementById("file-preview");
    const fileName = document.getElementById("file-name");
    const fileSize = document.getElementById("file-size");
    const removeBtn = document.getElementById("remove-file-btn");
    const uploadBtn = document.getElementById("upload-btn");
    const uploadStatus = document.getElementById("upload-status");
    const resultsSection = document.getElementById("results-section");
    const resultsFilename = document.getElementById("results-filename");
    const extractedText = document.getElementById("extracted-text");
    const copyTextBtn = document.getElementById("copy-text-btn");
    const skillsSection = document.getElementById("skills-section");
    const skillsCount = document.getElementById("skills-count");
    const skillsContainer = document.getElementById("skills-container");
    const scoreSection = document.getElementById("score-section");
    const scoreValue = document.getElementById("score-value");
    const scoreRingFill = document.getElementById("score-ring-fill");
    const scoreLevel = document.getElementById("score-level");
    const scoreReason = document.getElementById("score-reason");
    const riskSection = document.getElementById("risk-section");
    const riskCard = document.getElementById("risk-card");
    const riskIcon = document.getElementById("risk-icon");
    const riskLevelBadge = document.getElementById("risk-level-badge");
    const riskReasonEl = document.getElementById("risk-reason");
    const riskSugList = document.getElementById("risk-suggestions-list");
    const careerSection = document.getElementById("career-section");
    const careerContainer = document.getElementById("career-container");
    const simSection = document.getElementById("sim-section");
    const simSelect = document.getElementById("sim-skill-select");
    const simBtn = document.getElementById("sim-btn");
    const simResult = document.getElementById("sim-result");
    const simExplanation = document.getElementById("sim-explanation");
    const simNewRoles = document.getElementById("sim-new-roles");

    let selectedFile = null;
    let currentSkills = [];  // skills from last upload
    const dashboard = document.getElementById("dashboard");

    // ---------- Quick-stat elements ----------
    const qsSkills = document.getElementById("qs-skills");
    const qsScore = document.getElementById("qs-score");
    const qsRisk = document.getElementById("qs-risk");
    const qsRoles = document.getElementById("qs-roles");

    // ---------- Progress bar elements ----------
    const scoreProgressFill = document.getElementById("score-progress-fill");
    const scorePctLabel = document.getElementById("score-pct-label");

    // ---------- Collapsible toggle ----------
    const toggleTextBtn = document.getElementById("toggle-text-btn");
    const textCollapsible = document.getElementById("text-collapsible");
    if (toggleTextBtn && textCollapsible) {
        toggleTextBtn.addEventListener("click", () => {
            const isOpen = !textCollapsible.classList.contains("closed");
            textCollapsible.classList.toggle("closed", isOpen);
            toggleTextBtn.classList.toggle("collapsed", isOpen);
        });
    }

    // ---------- Download Report ----------
    const downloadBtn = document.getElementById("download-report-btn");
    if (downloadBtn) {
        downloadBtn.addEventListener("click", () => {
            window.location.href = "/download-report";
        });
    }

    // ---------- Click to browse ----------
    uploadArea.addEventListener("click", () => resumeInput.click());

    // ---------- File selected via input ----------
    resumeInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // ---------- Drag & Drop ----------
    uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.classList.add("drag-over");
    });

    uploadArea.addEventListener("dragleave", () => {
        uploadArea.classList.remove("drag-over");
    });

    uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.classList.remove("drag-over");
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // ---------- Handle selected file ----------
    function handleFile(file) {
        if (file.type !== "application/pdf") {
            showStatus("❌ Please select a PDF file.", "error");
            return;
        }

        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatSize(file.size);

        filePreview.classList.remove("hidden");
        uploadArea.classList.add("hidden");
        uploadBtn.disabled = false;

        uploadStatus.classList.add("hidden");
    }

    // ---------- Remove selected file ----------
    removeBtn.addEventListener("click", () => {
        resetUpload();
    });

    function resetUpload() {
        selectedFile = null;
        resumeInput.value = "";
        filePreview.classList.add("hidden");
        uploadArea.classList.remove("hidden");
        uploadBtn.disabled = true;
    }

    // ---------- Upload to server ----------
    uploadBtn.addEventListener("click", async () => {
        if (!selectedFile) return;

        uploadBtn.disabled = true;
        uploadBtn.textContent = "Analysing…";

        const formData = new FormData();
        formData.append("resume", selectedFile);

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (data.success) {
                showStatus(
                    `${data.message}  (${data.size_kb} KB)`,
                    "success"
                );

                // Show extracted text
                displayExtractedText(data.filename, data.extracted_text);

                // Show detected skills
                displaySkills(data.skills_categorized, data.skills_total);

                // Show resume score
                displayScore(data.score, data.score_level, data.score_reason, data.score_breakdown);

                // Show risk analysis
                displayRisk(data.risk_level, data.risk_icon, data.risk_reason, data.risk_suggestions);

                // Show career predictions
                displayCareer(data.career_predictions);

                // Show skill gap analysis
                if (data.skill_gap) displaySkillGap(data.skill_gap);

                // Enable simulator
                currentSkills = data.skills || [];
                showSimulator(currentSkills);

                resetUpload();
            } else {
                showStatus(`❌ ${data.message}`, "error");
            }
        } catch (err) {
            showStatus("❌ Network error — is the server running?", "error");
            console.error(err);
        } finally {
            uploadBtn.textContent = "Upload Resume";
        }
    });

    // ---------- Display extracted text ----------
    function displayExtractedText(name, text) {
        resultsFilename.textContent = "📄 " + name;
        extractedText.textContent = text;
        resultsSection.classList.remove("hidden");

        // Reveal dashboard on first result
        if (dashboard.classList.contains("hidden")) {
            dashboard.classList.remove("hidden");
        }

        setTimeout(() => {
            dashboard.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 200);
    }

    // ---------- Display detected skills ----------
    function displaySkills(categorized, total) {
        skillsCount.textContent = total;
        // Update quick-stat
        if (qsSkills) animateCount(qsSkills, 0, total, 600);
        skillsContainer.innerHTML = "";

        if (total === 0) {
            skillsContainer.innerHTML =
                '<p class="no-skills">No matching skills found. Try uploading a different resume.</p>';
            skillsSection.classList.remove("hidden");
            return;
        }

        // Color palette for categories
        const colors = [
            { bg: "rgba(99, 102, 241, 0.12)", border: "rgba(99, 102, 241, 0.3)", text: "#818cf8" },
            { bg: "rgba(168, 85, 247, 0.12)", border: "rgba(168, 85, 247, 0.3)", text: "#c084fc" },
            { bg: "rgba(56, 189, 248, 0.12)", border: "rgba(56, 189, 248, 0.3)", text: "#7dd3fc" },
            { bg: "rgba(52, 211, 153, 0.12)", border: "rgba(52, 211, 153, 0.3)", text: "#6ee7b7" },
            { bg: "rgba(251, 191, 36, 0.12)", border: "rgba(251, 191, 36, 0.3)", text: "#fcd34d" },
            { bg: "rgba(248, 113, 113, 0.12)", border: "rgba(248, 113, 113, 0.3)", text: "#fca5a5" },
            { bg: "rgba(244, 114, 182, 0.12)", border: "rgba(244, 114, 182, 0.3)", text: "#f9a8d4" },
            { bg: "rgba(167, 139, 250, 0.12)", border: "rgba(167, 139, 250, 0.3)", text: "#c4b5fd" },
        ];

        let colorIdx = 0;
        for (const [category, skills] of Object.entries(categorized)) {
            const color = colors[colorIdx % colors.length];
            colorIdx++;

            // Category group
            const group = document.createElement("div");
            group.className = "skill-group";

            // Category label
            const label = document.createElement("div");
            label.className = "skill-category-label";
            label.textContent = category;
            group.appendChild(label);

            // Skill tags
            const tagsWrap = document.createElement("div");
            tagsWrap.className = "skill-tags";

            skills.forEach((skill) => {
                const tag = document.createElement("span");
                tag.className = "skill-tag";
                tag.textContent = skill;
                tag.style.background = color.bg;
                tag.style.borderColor = color.border;
                tag.style.color = color.text;
                tagsWrap.appendChild(tag);
            });

            group.appendChild(tagsWrap);
            skillsContainer.appendChild(group);
        }

        skillsSection.classList.remove("hidden");
    }

    // ---------- Display resume score ----------
    function displayScore(score, level, reason, breakdown) {
        // Colour based on level
        const levelColors = {
            Low: { stroke: "#f87171", bg: "rgba(248,113,113,0.15)" },
            Medium: { stroke: "#fbbf24", bg: "rgba(251,191,36,0.15)" },
            High: { stroke: "#34d399", bg: "rgba(52,211,153,0.15)" },
            Excellent: { stroke: "#818cf8", bg: "rgba(129,140,248,0.15)" },
        };
        const color = levelColors[level] || levelColors.Medium;

        // Animate ring fill (circumference = 2 * π * 52 ≈ 326.73)
        const circumference = 326.73;
        const offset = circumference - (circumference * score) / 100;
        scoreRingFill.style.stroke = color.stroke;
        scoreRingFill.style.strokeDashoffset = offset;

        // Animate number count-up
        animateCount(scoreValue, 0, score, 800);

        // Level badge
        scoreLevel.textContent = level;
        scoreLevel.style.background = color.bg;
        scoreLevel.style.color = color.stroke;
        scoreLevel.style.borderColor = color.stroke;

        // Reason text
        scoreReason.textContent = reason;

        // Breakdown stats
        if (breakdown) {
            document.getElementById("bd-skill").textContent = breakdown.skill_score;
            document.getElementById("bd-diversity").textContent = "+" + breakdown.diversity_bonus;
            document.getElementById("bd-count").textContent = breakdown.skills_detected;
            document.getElementById("bd-cats").textContent = breakdown.categories_covered;
        }

        // Linear progress bar
        if (scoreProgressFill && scorePctLabel) {
            setTimeout(() => {
                scoreProgressFill.style.width = score + "%";
                scoreProgressFill.style.background = color.stroke;
            }, 150);
            scorePctLabel.textContent = score + "%";
        }

        // Quick-stat score
        if (qsScore) animateCount(qsScore, 0, score, 800);

        scoreSection.classList.remove("hidden");
    }

    // ---------- Count-up animation helper ----------
    function animateCount(el, from, to, duration) {
        const start = performance.now();
        function step(now) {
            const progress = Math.min((now - start) / duration, 1);
            el.textContent = Math.round(from + (to - from) * progress);
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    // ---------- Display risk analysis ----------
    function displayRisk(level, icon, reason, suggestions) {
        const riskColors = {
            High: { bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.35)", text: "#f87171" },
            Medium: { bg: "rgba(251,191,36,0.08)", border: "rgba(251,191,36,0.35)", text: "#fbbf24" },
            Low: { bg: "rgba(52,211,153,0.08)", border: "rgba(52,211,153,0.35)", text: "#34d399" },
        };
        const color = riskColors[level] || riskColors.Medium;

        // Card border colour
        riskCard.style.borderColor = color.border;
        riskCard.style.background =
            `linear-gradient(135deg, ${color.bg}, var(--surface))`;

        // Icon + badge
        riskIcon.textContent = icon;
        riskLevelBadge.textContent = level + " Risk";
        riskLevelBadge.style.background = color.bg;
        riskLevelBadge.style.color = color.text;
        riskLevelBadge.style.borderColor = color.border;

        // Reason
        riskReasonEl.textContent = reason;

        // Suggestions list
        riskSugList.innerHTML = "";
        suggestions.forEach((s) => {
            const li = document.createElement("li");
            li.textContent = s;
            riskSugList.appendChild(li);
        });

        // Quick-stat risk with color
        if (qsRisk) {
            qsRisk.textContent = level;
            qsRisk.style.color =
                level === "High" ? "#f87171" :
                    level === "Medium" ? "#fbbf24" : "#34d399";
        }

        riskSection.classList.remove("hidden");
    }

    // ---------- Display career predictions ----------
    function displayCareer(predictions) {
        careerContainer.innerHTML = "";

        if (!predictions || predictions.length === 0) {
            careerContainer.innerHTML =
                '<p class="no-skills">No career matches found. Try uploading a resume with more skills.</p>';
            careerSection.classList.remove("hidden");
            return;
        }

        predictions.forEach((pred, idx) => {
            const card = document.createElement("div");
            card.className = "career-card";
            card.style.animationDelay = (idx * 0.08) + "s";

            // Match colour
            let barColor;
            if (pred.match_percentage >= 60) barColor = "#34d399";
            else if (pred.match_percentage >= 30) barColor = "#fbbf24";
            else barColor = "#818cf8";

            card.innerHTML = `
                <div class="career-card-header">
                    <span class="career-icon">${pred.icon}</span>
                    <div class="career-title-wrap">
                        <h3 class="career-role">${pred.role}</h3>
                        <span class="career-pct" style="color:${barColor}">${pred.match_percentage}% match</span>
                    </div>
                </div>
                <div class="career-bar-track">
                    <div class="career-bar-fill" style="width:${pred.match_percentage}%;background:${barColor}"></div>
                </div>
                <div class="career-matched-skills">
                    ${pred.matched_skills.map(s => `<span class="career-skill-pill">${s}</span>`).join("")}
                </div>
                <p class="career-reason">${pred.reason}</p>
            `;

            careerContainer.appendChild(card);
        });

        // Quick-stat roles
        if (qsRoles) animateCount(qsRoles, 0, predictions.length, 500);

        careerSection.classList.remove("hidden");
    }

    // ---------- Display skill gap analysis ----------
    function displaySkillGap(gap) {
        const gapSection = document.getElementById("gap-section");
        if (!gapSection) return;

        // Target role
        document.getElementById("gap-icon").textContent = gap.target_icon;
        document.getElementById("gap-role").textContent = gap.target_role;

        // Gap progress bar (inverted: shows gap %)
        const fillEl = document.getElementById("gap-progress-fill");
        const pctEl = document.getElementById("gap-pct");
        setTimeout(() => { fillEl.style.width = gap.gap_percentage + "%"; }, 150);
        pctEl.textContent = gap.gap_percentage + "% gap (" + gap.matched_count + "/" + gap.total_role_skills + " matched)";

        // Summary
        const summaryEl = document.getElementById("gap-summary");
        // Convert **bold** markdown to <strong> for display
        summaryEl.innerHTML = gap.summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Missing skills
        const missingList = document.getElementById("gap-missing-list");
        const missingCount = document.getElementById("gap-missing-count");
        missingList.innerHTML = "";
        missingCount.textContent = gap.missing_skills.length;

        gap.missing_skills.forEach((item) => {
            const row = document.createElement("div");
            row.className = "gap-item";

            const badgeClass = item.priority === "High" ? "gap-badge-high" : "gap-badge-medium";
            row.innerHTML = `
                <span class="gap-item-skill">${item.skill}</span>
                <span class="gap-item-reason">${item.reason}</span>
                <span class="gap-item-badge ${badgeClass}">${item.priority}</span>
            `;
            missingList.appendChild(row);
        });

        // Recommended skills
        const recList = document.getElementById("gap-rec-list");
        const recCount = document.getElementById("gap-rec-count");
        recList.innerHTML = "";
        recCount.textContent = gap.recommended_skills.length;

        gap.recommended_skills.forEach((item) => {
            const row = document.createElement("div");
            row.className = "gap-item";
            row.innerHTML = `
                <span class="gap-item-skill">${item.skill}</span>
                <span class="gap-item-reason">${item.reason}</span>
                <span class="gap-item-badge gap-badge-rec">${item.icon}</span>
            `;
            recList.appendChild(row);
        });

        gapSection.classList.remove("hidden");
    }

    // ---------- Copy to clipboard ----------
    copyTextBtn.addEventListener("click", async () => {
        try {
            await navigator.clipboard.writeText(extractedText.textContent);
            copyTextBtn.textContent = "✅ Copied!";
            setTimeout(() => {
                copyTextBtn.textContent = "📋 Copy";
            }, 2000);
        } catch {
            copyTextBtn.textContent = "❌ Failed";
            setTimeout(() => {
                copyTextBtn.textContent = "📋 Copy";
            }, 2000);
        }
    });

    // ---------- Status message helper ----------
    function showStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = "upload-status " + type;
        uploadStatus.classList.remove("hidden");
    }

    // ---------- Utility ----------
    function formatSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / 1048576).toFixed(1) + " MB";
    }

    // ---------- Scroll-reveal for feature cards ----------
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = "1";
                    entry.target.style.transform = "translateY(0)";
                }
            });
        },
        { threshold: 0.15 }
    );

    document.querySelectorAll(".feature-card").forEach((card) => {
        observer.observe(card);
    });

    // ---------- Simulator: populate dropdown ----------
    async function showSimulator(skills) {
        try {
            const resp = await fetch("/api/all-skills");
            const data = await resp.json();
            simSelect.innerHTML = '<option value="">— Select a skill to add —</option>';

            const currentLower = new Set(skills.map(s => s.toLowerCase()));
            data.skills.forEach((skill) => {
                if (!currentLower.has(skill.toLowerCase())) {
                    const opt = document.createElement("option");
                    opt.value = skill;
                    opt.textContent = skill;
                    simSelect.appendChild(opt);
                }
            });

            simSection.classList.remove("hidden");
            simResult.classList.add("hidden");
        } catch (e) {
            console.error("Failed to load skills for simulator", e);
        }
    }

    // ---------- Simulator: enable button on select ----------
    simSelect.addEventListener("change", () => {
        simBtn.disabled = !simSelect.value;
    });

    // ---------- Simulator: run simulation ----------
    simBtn.addEventListener("click", async () => {
        const addedSkill = simSelect.value;
        if (!addedSkill) return;

        simBtn.disabled = true;
        simBtn.textContent = "Simulating…";

        try {
            const resp = await fetch("/simulate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    current_skills: currentSkills,
                    added_skill: addedSkill,
                }),
            });
            const data = await resp.json();

            if (data.success) {
                displaySimResult(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            simBtn.textContent = "Simulate Improvement";
            simBtn.disabled = false;
        }
    });

    // ---------- Simulator: display results ----------
    function displaySimResult(data) {
        simExplanation.textContent = data.improvement;

        document.getElementById("sim-before-score").textContent = data.before.score;
        document.getElementById("sim-before-level").textContent = data.before.level;
        document.getElementById("sim-before-risk").textContent = data.before.risk_icon + " " + data.before.risk;
        document.getElementById("sim-before-careers").textContent = data.before.careers;

        document.getElementById("sim-after-score").textContent = data.after.score;
        document.getElementById("sim-after-level").textContent = data.after.level;
        document.getElementById("sim-after-risk").textContent = data.after.risk_icon + " " + data.after.risk;
        document.getElementById("sim-after-careers").textContent = data.after.careers;

        // Highlight improvements
        const scoreEl = document.getElementById("sim-after-score");
        if (data.after.score > data.before.score) {
            scoreEl.style.color = "#34d399";
        } else {
            scoreEl.style.color = "";
        }

        // Show top career predictions after simulation
        simNewRoles.innerHTML = "";
        if (data.after.career_predictions && data.after.career_predictions.length) {
            const title = document.createElement("p");
            title.className = "sim-roles-title";
            title.textContent = "🚀 Top career paths after improvement:";
            simNewRoles.appendChild(title);

            data.after.career_predictions.forEach((pred) => {
                const tag = document.createElement("span");
                tag.className = "sim-role-tag";
                tag.textContent = pred.icon + " " + pred.role + " (" + pred.match_percentage + "%)";
                simNewRoles.appendChild(tag);
            });
        }

        simResult.classList.remove("hidden");
        simResult.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    console.log("✅ CareerForge AI loaded successfully.");
});
