/* ===== CareerForge AI — Premium Interactions ===== */

(function () {
    "use strict";

    /* ───── CUSTOM CURSOR ───── */
    const dot = document.querySelector(".cursor-dot");
    const ring = document.querySelector(".cursor-ring");
    if (dot && ring) {
        let mx = 0, my = 0, dx = 0, dy = 0;
        document.addEventListener("mousemove", (e) => { mx = e.clientX; my = e.clientY; });
        (function animCursor() {
            dx += (mx - dx) * 0.18; dy += (my - dy) * 0.18;
            dot.style.left = mx + "px"; dot.style.top = my + "px";
            ring.style.left = dx + "px"; ring.style.top = dy + "px";
            requestAnimationFrame(animCursor);
        })();
        document.querySelectorAll("a, button, .upload-zone, .viva-q, .sidebar-link, select, input").forEach((el) => {
            el.addEventListener("mouseenter", () => ring.classList.add("hover"));
            el.addEventListener("mouseleave", () => ring.classList.remove("hover"));
        });
    }

    /* ───── THREE.JS HERO ───── */
    const heroCanvas = document.getElementById("hero-canvas");
    if (heroCanvas && typeof THREE !== "undefined") {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, heroCanvas.clientWidth / heroCanvas.clientHeight, 0.1, 1000);
        camera.position.z = 30;
        const renderer = new THREE.WebGLRenderer({ canvas: heroCanvas, alpha: true, antialias: true });
        renderer.setSize(heroCanvas.clientWidth, heroCanvas.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        const particles = [];
        const geo = new THREE.IcosahedronGeometry(0.6, 0);
        const mat = new THREE.MeshBasicMaterial({ color: 0x00F5D4, wireframe: true, transparent: true, opacity: 0.35 });
        for (let i = 0; i < 80; i++) {
            const mesh = new THREE.Mesh(geo, mat.clone());
            mesh.position.set((Math.random() - 0.5) * 50, (Math.random() - 0.5) * 40, (Math.random() - 0.5) * 30);
            mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
            mesh.userData = { vx: (Math.random() - 0.5) * 0.01, vy: (Math.random() - 0.5) * 0.01, rSpeed: Math.random() * 0.005 + 0.002 };
            scene.add(mesh);
            particles.push(mesh);
        }

        let mouseX = 0, mouseY = 0;
        const heroSection = heroCanvas.parentElement;
        if (heroSection) {
            heroSection.addEventListener("mousemove", (e) => {
                mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
                mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
            });
        }

        function animateHero() {
            requestAnimationFrame(animateHero);
            particles.forEach((p) => {
                p.rotation.x += p.userData.rSpeed;
                p.rotation.y += p.userData.rSpeed * 0.7;
                p.position.x += p.userData.vx;
                p.position.y += p.userData.vy;
                if (Math.abs(p.position.x) > 28) p.userData.vx *= -1;
                if (Math.abs(p.position.y) > 22) p.userData.vy *= -1;
            });
            camera.position.x += (mouseX * 3 - camera.position.x) * 0.03;
            camera.position.y += (-mouseY * 3 - camera.position.y) * 0.03;
            camera.lookAt(scene.position);
            renderer.render(scene, camera);
        }
        animateHero();

        window.addEventListener("resize", () => {
            const w = heroCanvas.parentElement ? heroCanvas.parentElement.clientWidth : window.innerWidth;
            const h = heroCanvas.parentElement ? heroCanvas.parentElement.clientHeight : window.innerHeight;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        });
    }

    /* ───── WORD SWAP ───── */
    const swapContainer = document.querySelector(".word-swap");
    if (swapContainer) {
        const words = swapContainer.querySelectorAll(".word");
        let idx = 0;
        if (words.length) words[0].classList.add("active");
        setInterval(() => {
            words[idx].classList.remove("active");
            idx = (idx + 1) % words.length;
            words[idx].classList.add("active");
        }, 2200);
    }

    /* ───── INTERSECTION OBSERVER — Scroll reveals ───── */
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("visible"); } });
    }, { threshold: 0.15 });

    document.querySelectorAll(".reveal, .num-section, .feature-card").forEach((el) => revealObserver.observe(el));

    /* ───── SCROLL COUNTERS ───── */
    document.querySelectorAll("[data-count]").forEach((el) => {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((e) => {
                if (e.isIntersecting) {
                    const target = parseInt(el.dataset.count, 10);
                    const suffix = el.dataset.suffix || "";
                    let current = 0;
                    const step = Math.max(1, Math.floor(target / 60));
                    const timer = setInterval(() => {
                        current += step;
                        if (current >= target) { current = target; clearInterval(timer); }
                        el.textContent = current.toLocaleString() + suffix;
                    }, 22);
                    observer.unobserve(el);
                }
            });
        }, { threshold: 0.5 });
        observer.observe(el);
    });

    /* ───── COLLAPSIBLE TEXT SECTION ───── */
    const toggleBtn = document.getElementById("toggle-text-btn");
    const collapsible = document.getElementById("text-collapsible");
    if (toggleBtn && collapsible) {
        toggleBtn.addEventListener("click", () => {
            const icon = toggleBtn.querySelector(".collapse-icon");
            collapsible.classList.toggle("closed");
            if (icon) icon.textContent = collapsible.classList.contains("closed") ? "▸" : "▾";
        });
    }

    /* ───── STUDENT UPLOAD ───── */
    const uploadArea = document.getElementById("upload-area");
    const resumeInput = document.getElementById("resume-input");
    const filePreview = document.getElementById("file-preview");
    const fileName = document.getElementById("file-name");
    const fileSize = document.getElementById("file-size");
    const removeBtn = document.getElementById("remove-file-btn");
    const uploadBtn = document.getElementById("upload-btn");
    const uploadStatus = document.getElementById("upload-status");

    if (uploadArea && resumeInput) {
        uploadArea.addEventListener("click", () => resumeInput.click());
        uploadArea.addEventListener("dragover", (e) => { e.preventDefault(); uploadArea.classList.add("drag-over"); });
        uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("drag-over"));
        uploadArea.addEventListener("drop", (e) => {
            e.preventDefault(); uploadArea.classList.remove("drag-over");
            resumeInput.files = e.dataTransfer.files; showFilePreview();
        });
        resumeInput.addEventListener("change", showFilePreview);

        function showFilePreview() {
            if (!resumeInput.files.length) return;
            const f = resumeInput.files[0];
            if (fileName) fileName.textContent = f.name;
            if (fileSize) fileSize.textContent = (f.size / 1024).toFixed(1) + " KB";
            if (filePreview) filePreview.classList.remove("hidden");
            if (uploadArea) uploadArea.classList.add("hidden");
            if (uploadBtn) uploadBtn.disabled = false;
        }

        if (removeBtn) {
            removeBtn.addEventListener("click", () => {
                resumeInput.value = "";
                if (filePreview) filePreview.classList.add("hidden");
                if (uploadArea) uploadArea.classList.remove("hidden");
                if (uploadBtn) uploadBtn.disabled = true;
            });
        }

        if (uploadBtn) {
            uploadBtn.addEventListener("click", () => {
                if (!resumeInput.files.length) return;
                uploadBtn.disabled = true;
                uploadBtn.textContent = "Analyzing…";
                if (uploadStatus) { uploadStatus.classList.remove("hidden"); uploadStatus.textContent = "Processing your resume…"; uploadStatus.className = "upload-status"; }

                const fd = new FormData();
                fd.append("resume", resumeInput.files[0]);

                fetch("/upload", { method: "POST", body: fd })
                    .then((r) => r.json())
                    .then((data) => {
                        if (data.error) {
                            if (uploadStatus) { uploadStatus.textContent = data.error; uploadStatus.classList.add("error"); }
                            uploadBtn.textContent = "Upload Resume"; uploadBtn.disabled = false;
                            return;
                        }
                        if (uploadStatus) { uploadStatus.textContent = "Analysis complete!"; uploadStatus.classList.add("success"); }
                        displayResults(data);
                    })
                    .catch(() => {
                        if (uploadStatus) { uploadStatus.textContent = "Upload failed. Please try again."; uploadStatus.classList.add("error"); }
                        uploadBtn.textContent = "Upload Resume"; uploadBtn.disabled = false;
                    });
            });
        }
    }

    /* ───── DISPLAY RESULTS ───── */
    function displayResults(data) {
        const dashboard = document.getElementById("dashboard");
        if (dashboard) dashboard.classList.remove("hidden");

        displayText(data);
        displaySkills(data);
        displayScore(data);
        displayRisk(data);
        displayCareers(data);
        displayGap(data);
        displayExplainability(data);
        populateSimulator(data);
        updateQuickStats(data);

        if (dashboard) dashboard.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function displayText(data) {
        const el = document.getElementById("extracted-text");
        const fn = document.getElementById("results-filename");
        if (el) el.textContent = data.extracted_text || data.text || "No text extracted.";
        if (fn) fn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" width="16" height="16" style="vertical-align:-2px"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> ' + (data.filename || 'resume.pdf');
    }

    function displaySkills(data) {
        const container = document.getElementById("skills-container");
        const countEl = document.getElementById("skills-count");
        if (!container) return;
        container.innerHTML = "";
        const catSkills = data.skills_categorized || data.skills || {};
        let total = 0;
        // If it's an object with categories
        if (typeof catSkills === "object" && !Array.isArray(catSkills)) {
            for (const [cat, skills] of Object.entries(catSkills)) {
                if (!Array.isArray(skills) || !skills.length) continue;
                total += skills.length;
                const group = document.createElement("div");
                group.className = "skill-group";
                group.innerHTML = `<p class="skill-category-label">${cat}</p><div class="skill-tags">${skills.map((s) => `<span class="skill-tag">${s}</span>`).join("")}</div>`;
                container.appendChild(group);
            }
        } else if (Array.isArray(catSkills)) {
            total = catSkills.length;
            const group = document.createElement("div");
            group.className = "skill-group";
            group.innerHTML = `<div class="skill-tags">${catSkills.map((s) => `<span class="skill-tag">${s}</span>`).join("")}</div>`;
            container.appendChild(group);
        }
        if (countEl) countEl.textContent = data.skills_total || total;
    }

    function displayScore(data) {
        const score = data.score || 0;
        const scoreVal = document.getElementById("score-value");
        const ringFill = document.getElementById("score-ring-fill");
        const levelBadge = document.getElementById("score-level");
        const reasonEl = document.getElementById("score-reason");
        const pctLabel = document.getElementById("score-pct-label");
        const progressFill = document.getElementById("score-progress-fill");

        if (scoreVal) scoreVal.textContent = score;
        if (ringFill) {
            const circumference = 326.73;
            ringFill.style.strokeDashoffset = circumference - (score / 100) * circumference;
            if (score >= 70) ringFill.style.stroke = "var(--accent)";
            else if (score >= 40) ringFill.style.stroke = "var(--accent-warn)";
            else ringFill.style.stroke = "var(--accent-danger)";
        }
        const level = data.score_level || (score >= 70 ? "Excellent" : score >= 40 ? "Average" : "Low");
        if (levelBadge) {
            levelBadge.textContent = level;
            levelBadge.style.background = score >= 70 ? "rgba(0,245,212,.12)" : score >= 40 ? "rgba(255,182,39,.12)" : "rgba(255,77,109,.12)";
            levelBadge.style.color = score >= 70 ? "var(--accent)" : score >= 40 ? "var(--accent-warn)" : "var(--accent-danger)";
        }
        if (reasonEl) reasonEl.textContent = data.score_reason || "";
        if (pctLabel) pctLabel.textContent = score + "%";
        if (progressFill) progressFill.style.width = score + "%";

        const bdSkill = document.getElementById("bd-skill");
        const bdDiv = document.getElementById("bd-diversity");
        const bdCount = document.getElementById("bd-count");
        const bdCats = document.getElementById("bd-cats");
        const bd = data.score_breakdown || {};
        if (bdSkill) bdSkill.textContent = bd.skill_score || data.skill_score || 0;
        if (bdDiv) bdDiv.textContent = bd.diversity_bonus || data.diversity_bonus || 0;
        if (bdCount) bdCount.textContent = bd.skills_count || data.skills_total || data.skills_count || 0;
        if (bdCats) bdCats.textContent = bd.categories_count || data.categories_count || 0;

        /* ── Resume Strength Meter ── */
        const meterWrap = document.getElementById("strength-meter");
        if (meterWrap) {
            meterWrap.style.display = "block";
            const strengthLabel = score >= 80 ? "Excellent" : score >= 60 ? "Strong" : score >= 40 ? "Fair" : "Weak";
            meterWrap.innerHTML = `
                <div class="strength-label">Resume Strength: <strong>${strengthLabel}</strong></div>
                <div class="strength-bar-track">
                    <div class="strength-bar-fill" style="width:0%"></div>
                </div>
                <div class="strength-value">${score}/100</div>`;
            setTimeout(() => {
                const fill = meterWrap.querySelector(".strength-bar-fill");
                if (fill) fill.style.width = score + "%";
            }, 100);
        }
    }

    function displayRisk(data) {
        const risk = data.risk_level || "Unknown";
        const icon = document.getElementById("risk-icon");
        const badge = document.getElementById("risk-level-badge");
        const reason = document.getElementById("risk-reason");
        const list = document.getElementById("risk-suggestions-list");

        const colorMap = { High: "var(--accent-danger)", Medium: "var(--accent-warn)", Low: "var(--accent)" };
        const bgMap = { High: "rgba(255,77,109,.12)", Medium: "rgba(255,182,39,.12)", Low: "rgba(0,245,212,.12)" };

        if (icon) { icon.className = 'risk-dot risk-' + risk.toLowerCase(); }
        if (badge) { badge.textContent = risk; badge.style.color = colorMap[risk]; badge.style.background = bgMap[risk]; }
        if (reason) reason.textContent = data.risk_reason || "";
        if (list) {
            list.innerHTML = "";
            (data.risk_suggestions || []).forEach((s) => { const li = document.createElement("li"); li.textContent = s; list.appendChild(li); });
        }
    }

    function displayCareers(data) {
        const container = document.getElementById("career-container");
        if (!container) return;
        container.innerHTML = "";
        const predictions = data.career_predictions || [];
        const svgMonitor = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`;
        const svgGear = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`;
        const svgPalette = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></svg>`;
        const svgBarChart = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`;
        const svgCpu = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>`;
        const svgRocketRole = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M22 12A10 10 0 1 1 12 2"/><path d="M22 2L12 12"/><path d="M16 2h6v6"/></svg>`;
        const svgCloud = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>`;
        const svgSmartphone = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>`;
        const svgDatabase = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`;
        const svgShield = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;
        const svgBriefcase = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>`;
        const roleIcons = { "Full-Stack Developer": svgMonitor, "Backend Engineer": svgGear, "Frontend Developer": svgPalette, "Data Scientist": svgBarChart, "ML Engineer": svgCpu, "DevOps Engineer": svgRocketRole, "Cloud Architect": svgCloud, "Mobile Developer": svgSmartphone, "Database Administrator": svgDatabase, "Cybersecurity Analyst": svgShield };
        predictions.forEach((pred, i) => {
            const card = document.createElement("div");
            card.className = "career-card";
            card.style.animationDelay = (i * 0.08) + "s";
            const icon = roleIcons[pred.role] || svgBriefcase;
            const matchPct = pred.match ?? pred.match_percentage ?? 0;
            const barColor = matchPct >= 70 ? "var(--accent)" : matchPct >= 40 ? "var(--accent-warn)" : "var(--accent-danger)";
            const matchedSkills = (pred.matched_skills || []).map((s) => `<span class="career-skill-pill">${s}</span>`).join("");
            card.innerHTML = `
        <div class="career-card-header">
          <span class="career-icon">${icon}</span>
          <div class="career-title-wrap">
            <p class="career-role">${pred.role}</p>
          </div>
          <span class="career-pct" style="color:${barColor}">${matchPct}%</span>
        </div>
        <div class="career-bar-track"><div class="career-bar-fill" style="width:${matchPct}%;background:${barColor}"></div></div>
        ${matchedSkills ? `<div class="career-matched-skills">${matchedSkills}</div>` : ""}
        <p class="career-reason">${pred.reason || ""}</p>`;
            container.appendChild(card);
        });
    }

    function displayGap(data) {
        const gap = data.skill_gap || {};
        const roleEl = document.getElementById("gap-role");
        const iconEl = document.getElementById("gap-icon");
        const pctEl = document.getElementById("gap-pct");
        const fillEl = document.getElementById("gap-progress-fill");
        const summaryEl = document.getElementById("gap-summary");
        const missingList = document.getElementById("gap-missing-list");
        const missingCount = document.getElementById("gap-missing-count");
        const recList = document.getElementById("gap-rec-list");
        const recCount = document.getElementById("gap-rec-count");

        if (roleEl) roleEl.textContent = gap.target_role || "—";
        // iconEl is already set with SVG in the HTML template, no emoji needed
        const gapPct = gap.gap_percentage || 0;
        if (pctEl) pctEl.textContent = gapPct + "% gap";
        if (fillEl) fillEl.style.width = gapPct + "%";
        if (summaryEl) summaryEl.textContent = gap.summary || "";

        const missing = gap.missing_skills || [];
        if (missingCount) missingCount.textContent = missing.length;
        if (missingList) {
            missingList.innerHTML = "";
            missing.forEach((s) => {
                const item = document.createElement("div");
                item.className = "gap-item";
                const priority = s.priority || "Medium";
                const badgeClass = priority === "High" ? "gap-badge-high" : priority === "Medium" ? "gap-badge-medium" : "gap-badge-rec";
                item.innerHTML = `<span class="gap-item-skill">${s.skill || s}</span><span class="gap-item-reason">${s.reason || ""}</span><span class="gap-item-badge ${badgeClass}">${priority}</span>`;
                missingList.appendChild(item);
            });
        }

        const recs = gap.recommended_skills || [];
        if (recCount) recCount.textContent = recs.length;
        if (recList) {
            recList.innerHTML = "";
            recs.forEach((s) => {
                const item = document.createElement("div");
                item.className = "gap-item";
                item.innerHTML = `<span class="gap-item-skill">${s.skill || s}</span><span class="gap-item-reason">${s.reason || ""}</span><span class="gap-item-badge gap-badge-rec">Recommended</span>`;
                recList.appendChild(item);
            });
        }
    }

    function displayExplainability(data) {
        const container = document.getElementById("xai-container");
        const section = document.getElementById("xai-section");
        if (!container) return;
        container.innerHTML = "";

        const svgScore = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`;
        const svgRisk = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
        const svgBulb = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z"/></svg>`;
        const svgRocket = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M22 12A10 10 0 1 1 12 2"/><path d="M22 2L12 12"/><path d="M16 2h6v6"/></svg>`;
        const svgPuzzle = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>`;

        const matchPctFn = (p) => p.match ?? p.match_percentage ?? 0;
        const cards = [
            {
                icon: svgScore, title: "Score Analysis", type: "Reason",
                color: "var(--accent-secondary)", borderColor: "rgba(108,99,255,.4)",
                content: data.score_reason || "No score reasoning available.",
            },
            {
                icon: svgRisk, title: "Risk Assessment", type: "Insight",
                color: data.risk_level === "High" ? "var(--accent-danger)" : data.risk_level === "Low" ? "var(--accent)" : "var(--accent-warn)",
                borderColor: data.risk_level === "High" ? "rgba(255,77,109,.4)" : data.risk_level === "Low" ? "rgba(0,245,212,.4)" : "rgba(255,182,39,.4)",
                content: data.risk_reason || "No risk reasoning available.",
            },
            {
                icon: svgBulb, title: "Risk Mitigation", type: "Recommendation",
                color: "var(--accent-secondary)", borderColor: "rgba(108,99,255,.4)",
                content: (data.risk_suggestions || []).map((s) => "\u2022 " + s).join("\n") || "No suggestions.",
            },
            {
                icon: svgRocket, title: "Career Matching", type: "Insight",
                color: "var(--accent)", borderColor: "rgba(0,245,212,.4)",
                content: (data.career_predictions || []).slice(0, 3).map((p) => `${p.role} (${matchPctFn(p)}%): ${p.reason || ""}`).join("\n") || "No career insights.",
            },
            {
                icon: svgPuzzle, title: "Skill Gap Analysis", type: "Recommendation",
                color: "var(--accent-warn)", borderColor: "rgba(255,182,39,.4)",
                content: (data.skill_gap || {}).summary || "No skill gap data.",
            },
        ];

        cards.forEach((c, i) => {
            const card = document.createElement("div");
            card.className = "glass-card";
            card.style.cssText = `padding:18px 20px;border-left:3px solid ${c.borderColor};animation:fadeUp .4s ease ${i * 0.08}s both;`;
            card.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
          <div style="display:flex;align-items:center;gap:8px;font-weight:700;font-size:.92rem">${c.icon} ${c.title}</div>
          <span style="font-size:.68rem;font-weight:700;padding:2px 10px;border-radius:20px;background:rgba(255,255,255,.06);color:${c.color};text-transform:uppercase;letter-spacing:.5px">${c.type}</span>
        </div>
        <p style="font-size:.84rem;color:var(--text-muted);line-height:1.65;white-space:pre-line;margin:0">${c.content}</p>`;
            container.appendChild(card);
        });

        if (section) section.classList.remove("hidden");
    }

    /* ───── SIMULATOR ───── */
    let currentData = null;

    function populateSimulator(data) {
        currentData = data;
        const select = document.getElementById("sim-skill-select");
        const simBtn = document.getElementById("sim-btn");
        if (!select) return;
        select.innerHTML = '<option value="">— Select a skill to add —</option>';
        const allSkills = ["Python", "Java", "JavaScript", "React", "Angular", "Vue.js", "Node.js", "Django", "Flask", "Spring Boot", "Docker", "Kubernetes", "AWS", "Azure", "Go", "Rust", "TypeScript", "Swift", "Kotlin", "Ruby", "PHP", "C++", "C#", ".NET", "Terraform", "Jenkins", "GraphQL", "Redis", "PostgreSQL", "MongoDB", "TensorFlow", "PyTorch", "Hadoop", "Spark", "Tableau"];
        const userSkills = new Set();
        const skillsData = data.skills || [];
        if (Array.isArray(skillsData)) {
            skillsData.forEach((s) => userSkills.add(String(s).toLowerCase()));
        } else if (typeof skillsData === 'object') {
            for (const arr of Object.values(skillsData)) {
                if (Array.isArray(arr)) arr.forEach((s) => userSkills.add(String(s).toLowerCase()));
            }
        }
        allSkills.filter((s) => !userSkills.has(s.toLowerCase())).forEach((s) => { const opt = document.createElement("option"); opt.value = s; opt.textContent = s; select.appendChild(opt); });
        if (simBtn) {
            select.addEventListener("change", () => { simBtn.disabled = !select.value; });
            simBtn.addEventListener("click", () => runSimulation(select.value));
        }
    }

    function runSimulation(skill) {
        if (!skill || !currentData) return;
        const simBtn = document.getElementById("sim-btn");
        if (simBtn) { simBtn.disabled = true; simBtn.textContent = "Simulating…"; }

        // Flatten skills: may be a flat array or {category: [skills]} object
        let flatSkills = [];
        const rawSkills = currentData.skills || currentData.all_skills || [];
        if (Array.isArray(rawSkills)) {
            flatSkills = rawSkills;
        } else if (typeof rawSkills === "object") {
            for (const arr of Object.values(rawSkills)) {
                if (Array.isArray(arr)) flatSkills.push(...arr);
            }
        }

        fetch("/simulate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ added_skill: skill, current_skills: flatSkills }) })
            .then((r) => r.json())
            .then((sim) => {
                document.getElementById("sim-explanation").textContent = `Impact of adding "${skill}" to your profile:`;
                document.getElementById("sim-before-score").textContent = sim.before?.score ?? currentData.score;
                document.getElementById("sim-before-level").textContent = sim.before?.level ?? currentData.score_level;
                document.getElementById("sim-before-risk").textContent = sim.before?.risk ?? currentData.risk_level;
                document.getElementById("sim-before-careers").textContent = sim.before?.careers ?? (currentData.career_predictions || []).length;
                document.getElementById("sim-after-score").textContent = sim.after?.score ?? "—";
                document.getElementById("sim-after-level").textContent = sim.after?.level ?? "—";
                document.getElementById("sim-after-risk").textContent = sim.after?.risk ?? "—";
                document.getElementById("sim-after-careers").textContent = sim.after?.careers ?? "—";

                const rolesDiv = document.getElementById("sim-new-roles");
                if (rolesDiv && sim.new_roles && sim.new_roles.length) {
                    rolesDiv.innerHTML = `<p class="sim-roles-title">New career matches unlocked:</p>${sim.new_roles.map((r) => `<span class="sim-role-tag">${r}</span>`).join("")}`;
                }

                document.getElementById("sim-result").classList.remove("hidden");
                if (simBtn) { simBtn.textContent = "Simulate"; simBtn.disabled = false; }
            })
            .catch(() => { if (simBtn) { simBtn.textContent = "Simulate"; simBtn.disabled = false; } });
    }

    function updateQuickStats(data) {
        const qsSkills = document.getElementById("qs-skills");
        const qsScore = document.getElementById("qs-score");
        const qsRisk = document.getElementById("qs-risk");
        const qsRoles = document.getElementById("qs-roles");
        if (qsSkills) qsSkills.textContent = data.skills_total || data.skills_count || 0;
        if (qsScore) qsScore.textContent = data.score || 0;
        if (qsRisk) qsRisk.textContent = data.risk_level || "—";
        if (qsRoles) qsRoles.textContent = (data.career_predictions || []).length;
    }

    /* ───── COPY TEXT ───── */
    const copyBtn = document.getElementById("copy-text-btn");
    if (copyBtn) {
        copyBtn.addEventListener("click", () => {
            const text = document.getElementById("extracted-text")?.textContent;
            if (text) { navigator.clipboard.writeText(text); copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="20 6 9 17 4 12"/></svg> Copied!'; setTimeout(() => { copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy'; }, 1500); }
        });
    }

    /* ───── DOWNLOAD REPORT ───── */
    // Download button is now an <a> link to /download-report server route
    // No JS handler needed — the server generates a proper PDF

    /* ───── DEMO MODE AUTO-LOAD ───── */
    if (window.location.search.includes("demo=1")) {
        const banner = document.getElementById("demo-banner");
        if (banner) banner.classList.remove("hidden");
        fetch("/api/demo-data")
            .then((r) => r.json())
            .then((data) => displayResults(data))
            .catch((err) => console.error("Demo load failed:", err));
    }

    /* ───── VIVA ACCORDION ───── */
    document.querySelectorAll(".viva-q").forEach((q) => {
        q.addEventListener("click", () => {
            const answer = q.nextElementSibling;
            const icon = q.querySelector(".toggle-icon");
            const isOpen = answer.classList.contains("open");
            // Close all
            document.querySelectorAll(".viva-a.open").forEach((a) => a.classList.remove("open"));
            document.querySelectorAll(".viva-q.open").forEach((q2) => q2.classList.remove("open"));
            // Open this one if it was closed
            if (!isOpen) {
                answer.classList.add("open");
                q.classList.add("open");
            }
        });
    });

})();
