const { test, expect } = require("@playwright/test");

const TEST_PREFIX = `e2e-mm-${Date.now()}`;

// ---------------------------------------------------------------------------
// Smoke 1: App-Start und Status-Seite
// ---------------------------------------------------------------------------
test("App-Start und Status sind sichtbar", async ({ page }) => {
    await page.goto("/");

    await expect(page).toHaveTitle(/Micks Musikkiste/);
    await expect(page.locator("#page-dashboard")).toHaveClass(/active/);
    await expect(page.getByRole("heading", { name: "Micks Musikkiste", exact: true })).toBeVisible();
    await expect(page.locator("#recentProjects")).toBeVisible();

    // Zur Status-Seite navigieren
    await page.locator(".nav-btn[data-page='status']").click();
    await expect(page.locator("#page-status")).toHaveClass(/active/);
    await expect(page.locator("#statusEngine")).toContainText(/mock/i);
});

// ---------------------------------------------------------------------------
// Smoke 2: Beat generieren, Projekt speichern, Export, Projektliste
// ---------------------------------------------------------------------------
test("Beat generieren, Projekt speichern, Export und Projektliste (V2 Mock)", async ({ page }) => {
    const beatTitle = `${TEST_PREFIX}-beat`;
    const projectName = `${TEST_PREFIX}-projekt`;
    const exportName = `${TEST_PREFIX}-export`;

    await page.goto("/");

    // Zur Beat-Seite
    await page.locator(".nav-btn[data-page='beat']").click();
    await expect(page.locator("#page-beat")).toHaveClass(/active/);

    // Formular ausfüllen (V2-IDs)
    await page.locator("#beatTitle").fill(beatTitle);
    // Genre-Dropdown wartet auf API-Befüllung — direkt via value setzen
    await page.locator("#beatGenre").selectOption({ index: 1 });
    await page.locator("#beatPrompt").fill("dark industrial kick hypnotic groove E2E test");
    await page.locator("#beatBpm").fill("128");
    // Sende Formular
    await page.locator("#beatForm button[type='submit']").click();

    // Warte auf Ergebnis-Seite und Job-Abschluss
    await expect(page.locator("#page-result")).toHaveClass(/active/);
    await expect(page.locator("#resultTitle")).not.toContainText("Ergebnis", { timeout: 30_000 });
    await expect(page.locator("#audioPlayer")).toHaveAttribute("src", /\/outputs\//, { timeout: 30_000 });

    // Projekt speichern
    await page.getByTestId("save-project-btn").click();
    await expect(page.getByTestId("text-input-dialog")).toBeVisible();
    await page.getByTestId("text-input-field").fill(projectName);
    await page.getByTestId("text-input-confirm").click();
    await expect(page.locator(".toast-success")).toContainText("Projekt gespeichert", { timeout: 8_000 });

    // Exportieren
    const downloadPromise = page.waitForEvent("download", { timeout: 15_000 });
    await page.getByTestId("export-result-btn").click();
    await expect(page.getByTestId("text-input-dialog")).toBeVisible();
    await page.getByTestId("text-input-field").fill(exportName);
    await page.getByTestId("text-input-confirm").click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBeTruthy();
    await expect(page.locator(".toast-success")).toContainText(/export/i, { timeout: 8_000 });

    // Projektliste prüfen
    await page.locator(".nav-btn[data-page='projects']").click();
    await expect(page.locator("#page-projects")).toHaveClass(/active/);
    await expect(page.locator("#projectsList .project-card").first()).toBeVisible({ timeout: 8_000 });
    await page.locator("#projectSearch").fill(projectName);
    await expect(page.locator("#projectsList .project-card").first()).toContainText(projectName, { timeout: 5_000 });

    // Status-Seite: Projekte-Zähler nicht leer
    await page.locator(".nav-btn[data-page='status']").click();
    await expect(page.locator("#page-status")).toHaveClass(/active/);
    await expect(page.locator("#statusProjects")).not.toBeEmpty({ timeout: 5_000 });
});

// ---------------------------------------------------------------------------
// Smoke 3: Navigation und Dashboard-Quickstart (V2)
// ---------------------------------------------------------------------------
test("Navigation und Dashboard-Quickstart landen auf richtigen Seiten (V2)", async ({ page }) => {
    await page.goto("/");

    // Dashboard ist Startseite
    await expect(page.locator(".nav-btn[data-page='dashboard']")).toHaveClass(/active/);

    // Quickstart: Beat-Karte im Dashboard klicken
    await page.locator(".start-card[data-page='beat']").click();
    await expect(page.locator("#page-beat")).toHaveClass(/active/);
    await expect(page.locator(".nav-btn[data-page='beat']")).toHaveClass(/active/);

    // Zurück zum Dashboard über Nav
    await page.locator(".nav-btn[data-page='dashboard']").click();
    await expect(page.locator("#page-dashboard")).toHaveClass(/active/);

    // Quickstart: Track-Karte im Dashboard klicken
    await page.locator(".start-card[data-page='track']").click();
    await expect(page.locator("#page-track")).toHaveClass(/active/);
    await expect(page.locator(".nav-btn[data-page='track']")).toHaveClass(/active/);

    // Track-Formular hat V2-Felder (kein Preset, kein Mood)
    await expect(page.locator("#trackGenre")).toBeVisible();
    await expect(page.locator("#trackPrompt")).toBeVisible();
    await expect(page.locator("#trackTextIdea")).toBeVisible();
    // V1-Felder dürfen nicht existieren
    await expect(page.locator("#trackMood")).not.toBeAttached();
    await expect(page.locator("#trackLyrics")).not.toBeAttached();
    await expect(page.locator("#trackPreset")).not.toBeAttached();

    // Beat-Formular: ebenfalls V2-Felder
    await page.locator(".nav-btn[data-page='beat']").click();
    await expect(page.locator("#beatGenre")).toBeVisible();
    await expect(page.locator("#beatPrompt")).toBeVisible();
    await expect(page.locator("#beatBpm")).toBeVisible();
    // V1-Feld existiert nicht
    await expect(page.locator("#beatPreset")).not.toBeAttached();
});
