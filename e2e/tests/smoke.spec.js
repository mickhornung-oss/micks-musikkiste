const { test, expect } = require("@playwright/test");

const TEST_PREFIX = `e2e-mm-${Date.now()}`;

test("App-Start und Status sind sichtbar", async ({ page }) => {
    await page.goto("/");

    await expect(page).toHaveTitle(/Micks Musikkiste/);
    await expect(page.locator("#page-dashboard")).toHaveClass(/active/);
    await expect(page.getByRole("heading", { name: "Micks Musikkiste", exact: true })).toBeVisible();
    await expect(page.locator("#recentProjects")).toBeVisible();

    await page.getByRole("button", { name: "Status" }).click();
    await expect(page.locator("#page-status")).toHaveClass(/active/);
    await expect(page.locator("#statusEngine")).toContainText(/mock/i);
});

test("Mock-Track, Projekt, Export und Listenfluss laufen im Browser", async ({ page }) => {
    const trackTitle = `${TEST_PREFIX}-track`;
    const projectName = `${TEST_PREFIX}-project`;
    const exportName = `${TEST_PREFIX}-export`;

    await page.goto("/");
    await page.getByRole("button", { name: "Voller Track" }).click();
    await expect(page.locator("#page-track")).toHaveClass(/active/);

    await page.locator("#trackTitle").fill(trackTitle);
    await page.locator("#trackMood").selectOption("dark");
    await page.locator("#trackDuration").selectOption("30");
    await page.locator("#trackLyrics").fill("E2E Smoke");
    await page.locator("#trackPreset").selectOption("techno_dark");
    await page.locator("#trackForm button[type='submit']").click();

    await expect(page.locator("#page-result")).toHaveClass(/active/);
    await expect(page.locator("#resultTitle")).toContainText(trackTitle, { timeout: 25_000 });
    await expect(page.locator("#audioPlayer")).toHaveAttribute("src", /\/outputs\//);

    await page.getByTestId("save-project-btn").click();
    await expect(page.getByTestId("text-input-dialog")).toBeVisible();
    await page.getByTestId("text-input-field").fill(projectName);
    await page.getByTestId("text-input-confirm").click();
    await expect(page.locator(".toast-success").last()).toContainText("Projekt gespeichert");

    const downloadPromise = page.waitForEvent("download");
    await page.getByTestId("export-result-btn").click();
    await expect(page.getByTestId("text-input-dialog")).toBeVisible();
    await page.getByTestId("text-input-field").fill(exportName);
    await page.getByTestId("text-input-confirm").click();
    const download = await downloadPromise;
    await expect(page.locator(".toast-success").last()).toContainText(/export/i);
    expect(download.suggestedFilename()).toContain(exportName);

    await page.getByRole("button", { name: "Projekte" }).click();
    await expect(page.locator("#page-projects")).toHaveClass(/active/);
    await page.locator("#projectSearch").fill(projectName);
    await expect(page.locator("#projectsList .project-card").first()).toContainText(projectName);

    await page.getByTestId("project-export-btn").first().click();
    await expect(page.locator(".toast-success").last()).toContainText(/export/i);
    await expect(page.locator("#projectsList .project-card").first()).toContainText(projectName);

    await page.getByRole("button", { name: "Status" }).click();
    await expect(page.locator("#page-status")).toHaveClass(/active/);
    await expect(page.locator("#statusProjects")).not.toBeEmpty();
});

test("Quickstart und Topbar landen in denselben konsistenten Modus-Zustaenden", async ({ page }) => {
    await page.goto("/");

    await expect(page.locator(".nav-btn[data-page='dashboard']")).toHaveClass(/active/);
    await expect(page.locator(".nav-btn[data-mode].active")).toHaveCount(0);

    await page.locator(".action-card[data-mode='full_track']").click();
    await expect(page.locator("#page-track")).toHaveClass(/active/);
    await expect(page.locator(".nav-btn[data-mode='full_track']")).toHaveClass(/active/);
    await expect(page.locator("#trackPreset")).toHaveValue("techno_melodic");
    await expect(page.locator("#trackMood")).toHaveValue("energetic");

    await page.getByRole("button", { name: "Start" }).click();
    await expect(page.locator("#page-dashboard")).toHaveClass(/active/);
    await expect(page.locator(".nav-btn[data-page='dashboard']")).toHaveClass(/active/);

    await page.getByRole("button", { name: "Hip-Hop Beat" }).click();
    await expect(page.locator("#page-beat")).toHaveClass(/active/);
    await expect(page.locator(".nav-btn[data-mode='hiphop_beat']")).toHaveClass(/active/);
    await expect(page.locator("#beatPageTitle")).toContainText("Hip-Hop Beat");
    await expect(page.locator("#beatPreset")).toHaveValue("beat_hiphop_trap");
    await expect(page.locator(".mode-chip[data-mode='hiphop_beat']")).toHaveClass(/active/);

    await page.locator(".mode-chip[data-mode='techno_beat']").click();
    await expect(page.locator("#beatPageTitle")).toContainText("Techno Beat");
    await expect(page.locator("#beatPreset")).toHaveValue("beat_techno_club");
    await expect(page.locator(".mode-chip[data-mode='techno_beat']")).toHaveClass(/active/);
});
