// Global variables
let selectedDates = [];
let seancesData = {};
let enseignantsList = [];
let confirmationCallback = null;

// Calendar variables
let currentCalendarDate = new Date();
let clickedCalendarDate = null;

// Initialize the application
$(document).ready(function () {
  initializeApp();
  setupEventListeners();
});

async function initializeApp() {
  try {
    const result = await eel.initialize_app()();
    if (result.success) {
      console.log("App initialized successfully");
      console.log("Seances info:", result.seances_info);

      // Load existing dates if any
      const dates = await eel.get_available_dates()();
      console.log("Available dates:", dates);
      selectedDates = dates || [];

      // Clear existing tables first
      $("#seancesContainer").empty();
      seancesData = {};

      // Sort dates before loading seances
      selectedDates.sort((a, b) => {
        const dateA = new Date(a.split("/").reverse().join("-"));
        const dateB = new Date(b.split("/").reverse().join("-"));
        return dateA - dateB;
      });

      // Load each date's seances in sorted order
      for (const date of selectedDates) {
        console.log("Loading seances for date:", date);
        await loadSeancesForDate(date);
      }

      // Load enseignants list
      enseignantsList = await eel.get_enseignants_list()();
      console.log("Loaded enseignants:", enseignantsList.length);

      // Initialize calendar
      initializeCalendar();
    } else {
      console.error("Failed to initialize app:", result.error);
      showMessage(
        "Error",
        "Failed to initialize application: " + result.error,
        "error",
      );
    }
  } catch (error) {
    console.error("Error initializing app:", error);
    showMessage("Error", "Error initializing application: " + error, "error");
  }
}

function setupEventListeners() {
  // No longer needed - calendar handles date selection
}

// Calendar Functions
function initializeCalendar() {
  renderCalendar();
}

function renderCalendar() {
  const year = currentCalendarDate.getFullYear();
  const month = currentCalendarDate.getMonth();

  // Update month/year header
  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  $("#calendarMonthYear").text(`${monthNames[month]} ${year}`);

  // Clear calendar days
  $("#calendarDays").empty();

  // Get first day of month and number of days
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startingDayOfWeek = firstDay.getDay();

  // Get previous month's last few days
  const prevMonth = new Date(year, month, 0);
  const daysInPrevMonth = prevMonth.getDate();

  // Add previous month's trailing days
  for (let i = startingDayOfWeek - 1; i >= 0; i--) {
    const day = daysInPrevMonth - i;
    const dayElement = createCalendarDay(
      day,
      true,
      new Date(year, month - 1, day),
    );
    $("#calendarDays").append(dayElement);
  }

  // Add current month's days
  for (let day = 1; day <= daysInMonth; day++) {
    const dayElement = createCalendarDay(
      day,
      false,
      new Date(year, month, day),
    );
    $("#calendarDays").append(dayElement);
  }

  // Add next month's leading days
  const totalCells = $("#calendarDays").children().length;
  const remainingCells = 42 - totalCells; // 6 rows × 7 days = 42 cells
  for (let day = 1; day <= remainingCells; day++) {
    const dayElement = createCalendarDay(
      day,
      true,
      new Date(year, month + 1, day),
    );
    $("#calendarDays").append(dayElement);
  }
}

function createCalendarDay(day, isOtherMonth, fullDate) {
  const dayElement = $(
    `<div class="calendar-day ${isOtherMonth ? "other-month" : ""}" data-date="${fullDate.toISOString().split("T")[0]}">${day}</div>`,
  );

  // Check if this date is today
  const today = new Date();
  if (fullDate.toDateString() === today.toDateString()) {
    dayElement.addClass("today");
  }

  // Check if this date is selected
  const dateStr = formatDateToDDMMYYYY(fullDate);
  if (selectedDates.includes(dateStr)) {
    dayElement.addClass("selected-date");
  }

  // Add click handler
  dayElement.click(function () {
    if (!isOtherMonth) {
      handleCalendarDayClick(fullDate);
    }
  });

  return dayElement;
}

function handleCalendarDayClick(date) {
  // Remove previous clicked styling
  $(".calendar-day").removeClass("clicked-date");

  // Add clicked styling to current day
  $(`[data-date="${date.toISOString().split("T")[0]}"]`).addClass(
    "clicked-date",
  );

  clickedCalendarDate = date;
  const dateStr = formatDateToDDMMYYYY(date);

  // Update selected date info
  $("#selectedDateText").text(dateStr);
  $("#selectedDateInfo").show();

  // Update button states
  if (selectedDates.includes(dateStr)) {
    // Date is already selected
    $("#selectDateBtn").hide();
    $("#showSeancesBtn").show();
    $("#removeDateBtn").show();
  } else {
    // Date is not selected
    $("#selectDateBtn").show();
    $("#showSeancesBtn").hide();
    $("#removeDateBtn").hide();
  }

  // Enable the select button
  $("#selectDateBtn").prop("disabled", false);
}

function formatDateToDDMMYYYY(date) {
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}

function previousMonth() {
  currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
  renderCalendar();
}

function nextMonth() {
  currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
  renderCalendar();
}

function selectCurrentDate() {
  if (clickedCalendarDate) {
    const dateStr = formatDateToDDMMYYYY(clickedCalendarDate);
    if (!selectedDates.includes(dateStr)) {
      addExamDateFromCalendar(dateStr);
    }
  }
}

function showSeancesForDate() {
  if (clickedCalendarDate) {
    const dateStr = formatDateToDDMMYYYY(clickedCalendarDate);
    scrollToSeancesTable(dateStr);
  }
}

function removeSelectedDate() {
  if (clickedCalendarDate) {
    const dateStr = formatDateToDDMMYYYY(clickedCalendarDate);
    removeExamDate(dateStr);
  }
}

function scrollToSeancesTable(date) {
  const safeDate = date.replace(/[^a-zA-Z0-9]/g, "_");
  const tableElement = $(`#seanceTable_${safeDate}`);

  if (tableElement.length > 0) {
    $("html, body").animate(
      {
        scrollTop: tableElement.closest(".card").offset().top - 100,
      },
      800,
    );
  } else {
    showMessage("Info", "No seances found for this date", "info");
  }
}

function removeExamDateFromTable(date) {
  removeExamDate(date);
}

function showInCalendar(dateStr) {
  // Parse the DD/MM/YYYY date string
  const parts = dateStr.split("/");
  const targetDate = new Date(
    parseInt(parts[2]),
    parseInt(parts[1]) - 1,
    parseInt(parts[0]),
  );

  // Set calendar to show the target date's month
  currentCalendarDate = new Date(
    targetDate.getFullYear(),
    targetDate.getMonth(),
    1,
  );
  renderCalendar();

  // Simulate clicking on the date
  setTimeout(() => {
    handleCalendarDayClick(targetDate);

    // Scroll to calendar
    $("html, body").animate(
      {
        scrollTop: $(".calendar-container").offset().top - 100,
      },
      800,
    );
  }, 100);
}

async function addExamDateFromCalendar(dateStr) {
  try {
    // Convert DD/MM/YYYY to YYYY-MM-DD for the backend
    const parts = dateStr.split("/");
    const isoDate = `${parts[2]}-${parts[1]}-${parts[0]}`;

    const result = await eel.add_exam_date(isoDate)();
    if (result.success) {
      selectedDates.push(result.formatted_date);
      selectedDates.sort((a, b) => {
        const dateA = new Date(a.split("/").reverse().join("-"));
        const dateB = new Date(b.split("/").reverse().join("-"));
        return dateA - dateB;
      });

      renderCalendar(); // Refresh calendar to show selected date
      await loadSeancesForDate(result.formatted_date);

      // Update button states
      $("#selectDateBtn").hide();
      $("#showSeancesBtn").show();
      $("#removeDateBtn").show();

      showMessage(
        "Success",
        `Date ${result.formatted_date} added successfully`,
        "success",
      );
    } else {
      showMessage("Error", "Failed to add date: " + result.error, "error");
    }
  } catch (error) {
    console.error("Error adding date:", error);
    showMessage("Error", "Error adding date: " + error, "error");
  }
}

async function addExamDate(date) {
  try {
    const result = await eel.add_exam_date(date)();
    if (result.success) {
      // Use the formatted date returned from the server
      const formattedDate = result.formatted_date;
      selectedDates.push(formattedDate);
      // Sort by date value
      selectedDates.sort((a, b) => {
        const dateA = new Date(a.split("/").reverse().join("-"));
        const dateB = new Date(b.split("/").reverse().join("-"));
        return dateA - dateB;
      });
      updateSelectedDatesDisplay();
      await loadSeancesForDate(formattedDate);
      $("#newDate").val("");
    } else {
      showMessage("Error", "Failed to add date: " + result.error, "error");
    }
  } catch (error) {
    console.error("Error adding date:", error);
    showMessage("Error", "Error adding date: " + error, "error");
  }
}

async function removeExamDate(date) {
  showConfirmation(
    "Remove Date",
    `Are you sure you want to remove the date ${date} and all its seances?`,
    async function () {
      try {
        const result = await eel.remove_exam_date(date)();
        if (result.success) {
          selectedDates = selectedDates.filter((d) => d !== date);
          $(`#seanceTable_${date.replace(/[^a-zA-Z0-9]/g, "_")}`)
            .closest(".card")
            .remove();
          delete seancesData[date];

          // Refresh calendar to remove selected styling
          renderCalendar();

          // Update button states
          $("#selectDateBtn").show();
          $("#showSeancesBtn").hide();
          $("#removeDateBtn").hide();

        } else {
          showMessage(
            "Error",
            "Failed to remove date: " + result.error,
            "error",
          );
        }
      } catch (error) {
        console.error("Error removing date:", error);
        showMessage("Error", "Error removing date: " + error, "error");
      }
    },
  );
}

async function loadSeancesForDate(date) {
  try {
    const seances = await eel.get_seances_for_date(date)();
    console.log(`Loaded ${seances.length} seances for date ${date}:`, seances);
    seancesData[date] = seances || [];
    createSeanceTable(date, seances || []);
  } catch (error) {
    console.error("Error loading seances for date:", error);
    seancesData[date] = [];
    createSeanceTable(date, []);
  }
}

function createSeanceTable(date, seances) {
  const safeDate = date.replace(/[^a-zA-Z0-9]/g, "_");
  const existingTable = $(`#seanceTable_${safeDate}`);

  if (existingTable.length) {
    // Update existing table
    updateSeanceTable(safeDate, seances);
    return;
  }

  const tableHtml = `
          <div class="card shadow mb-4">
            <div class="card-header py-3">
              <h6 class="m-0 font-weight-bold text-primary">
                Seances for ${date}
                <div class="float-right">
                  <button class="btn btn-sm btn-info mr-2" onclick="showInCalendar('${date}')" title="Show this date in calendar">
                    <i class="fas fa-calendar-alt"></i>
                  </button>
                  <button class="btn btn-sm btn-success mr-2" onclick="addNewSeance('${date}')">
                    <i class="fas fa-plus"></i> Add Seance
                  </button>
                  <button class="btn btn-sm btn-danger" onclick="removeExamDateFromTable('${date}')">
                    <i class="fas fa-trash"></i> Remove Date
                  </button>
                </div>
              </h6>
            </div>
            <div class="card-body">
              <div class="table-responsive">
                <table class="table table-bordered" id="seanceTable_${safeDate}" width="100%" cellspacing="0">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Start Time</th>
                      <th>End Time</th>
                      <th>Rooms</th>
                      <th>Teachers</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody id="seanceTableBody_${safeDate}">
                    <!-- Seances will be populated here -->
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        `;

  $("#seancesContainer").append(tableHtml);
  updateSeanceTable(safeDate, seances);

  // Initialize DataTable after a short delay to ensure DOM is ready
  setTimeout(() => {
    try {
      $(`#seanceTable_${safeDate}`).DataTable({
        pageLength: 10,
        responsive: true,
        destroy: true, // Allow re-initialization
      });
    } catch (error) {
      console.warn("DataTable initialization failed:", error);
    }
  }, 100);
}

function updateSeanceTable(safeDate, seances) {
  const tableId = `seanceTable_${safeDate}`;
  const tbody = $(`#seanceTableBody_${safeDate}`);

  // Destroy existing DataTable if it exists
  if ($.fn.DataTable.isDataTable(`#${tableId}`)) {
    $(`#${tableId}`).DataTable().destroy();
  }

  tbody.empty();

  // Get the original date from safeDate
  const originalDate = safeDate.replace(/_/g, "/");

  seances.forEach((seance, index) => {
    const row = $(`
            <tr>
              <td>${seance.name}</td>
              <td>${seance.h_debut}</td>
              <td>${seance.h_fin}</td>
              <td>${seance.salles.join(", ")}</td>
              <td>${seance.enseignants.join(", ")}</td>
              <td>
                <button class="btn btn-sm btn-warning" onclick="editSeance('${originalDate}', ${index})">
                  <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger ml-1" onclick="deleteSeance('${originalDate}', ${index})">
                  <i class="fas fa-trash"></i>
                </button>
              </td>
            </tr>
          `);
    tbody.append(row);
  });

  // Re-initialize DataTable
  setTimeout(() => {
    try {
      $(`#${tableId}`).DataTable({
        pageLength: 10,
        responsive: true,
      });
    } catch (error) {
      console.warn("DataTable re-initialization failed:", error);
    }
  }, 100);
}

// Global variable to store the current date for adding seance
let currentAddSeanceDate = null;

// Global arrays to store teachers and rooms for the current seance
let currentTeachers = [];
let currentRooms = [];

async function addNewSeance(date) {
  currentAddSeanceDate = date;

  // Clear the form and arrays
  $("#addSeanceForm")[0].reset();
  currentTeachers = [];
  currentRooms = [];

  // Clear containers
  $("#teachersContainer").empty();
  $("#roomsContainer").empty();

  // Update modal title
  $("#addSeanceModalLabel").text(`Add New Seance for ${date}`);

  // Show the modal
  $("#addSeanceModal").modal("show");
}

function addTeacher() {
  const input = $("#teacherInput");
  const teacherCode = input.val().trim();

  if (!teacherCode) {
    showMessage("Error", "Please enter a teacher code", "error");
    return;
  }

  // Validate that it's a number
  if (!/^\d+$/.test(teacherCode)) {
    showMessage("Error", "Teacher code must be a number", "error");
    return;
  }

  const teacherNum = parseInt(teacherCode);

  // Check if teacher already exists
  if (currentTeachers.includes(teacherNum)) {
    showMessage("Warning", "Teacher already added", "warning");
    return;
  }

  // Add teacher to array and display
  currentTeachers.push(teacherNum);
  displayTeachers();
  input.val("");
}

function addRoom() {
  const input = $("#roomInput");
  const roomCode = input.val().trim();

  if (!roomCode) {
    showMessage("Error", "Please enter a room code", "error");
    return;
  }

  // Check if room already exists
  if (currentRooms.includes(roomCode)) {
    showMessage("Warning", "Room already added", "warning");
    return;
  }

  // Add room to array and display
  currentRooms.push(roomCode);
  displayRooms();
  input.val("");
}

function displayTeachers() {
  const container = $("#teachersContainer");
  container.empty();

  if (currentTeachers.length === 0) {
    container.append('<p class="text-muted">No teachers added</p>');
    return;
  }

  currentTeachers.forEach((teacher) => {
    const badge = $(`
            <span class="badge badge-info mr-2 mb-2" style="font-size: 0.9rem;">
              ${teacher}
              <button type="button" class="btn btn-sm ml-1" style="color: white; background: none; border: none; padding: 0;" onclick="removeTeacher(${teacher})">
                <i class="fas fa-times"></i>
              </button>
            </span>
          `);
    container.append(badge);
  });
}

function displayRooms() {
  const container = $("#roomsContainer");
  container.empty();

  if (currentRooms.length === 0) {
    container.append('<p class="text-muted">No rooms added</p>');
    return;
  }

  currentRooms.forEach((room) => {
    const badge = $(`
            <span class="badge badge-success mr-2 mb-2" style="font-size: 0.9rem;">
              ${room}
              <button type="button" class="btn btn-sm ml-1" style="color: white; background: none; border: none; padding: 0;" onclick="removeRoom('${room}')">
                <i class="fas fa-times"></i>
              </button>
            </span>
          `);
    container.append(badge);
  });
}

function removeTeacher(teacherCode) {
  currentTeachers = currentTeachers.filter((t) => t !== teacherCode);
  displayTeachers();
}

function removeRoom(roomCode) {
  currentRooms = currentRooms.filter((r) => r !== roomCode);
  displayRooms();
}

// Allow adding teachers/rooms with Enter key
$(document).ready(function () {
  $("#teacherInput").keypress(function (e) {
    if (e.which === 13) {
      // Enter key
      addTeacher();
    }
  });

  $("#roomInput").keypress(function (e) {
    if (e.which === 13) {
      // Enter key
      addRoom();
    }
  });
});

async function saveNewSeance() {
  const startTime = $("#seanceStartTime").val();
  const endTime = $("#seanceEndTime").val();

  if (!startTime || !endTime) {
    showMessage("Error", "Please enter both start and end times", "error");
    return;
  }

  // Convert time format from HH:MM to HH:MM:SS
  const h_debut = startTime + ":00";
  const h_fin = endTime + ":00";

  try {
    const result = await eel.add_seance_to_date(
      currentAddSeanceDate,
      h_debut,
      h_fin,
      currentRooms,
      currentTeachers,
    )();
    if (result.success) {
      $("#addSeanceModal").modal("hide");
      await loadSeancesForDate(currentAddSeanceDate);
      showMessage("Success", "Seance added successfully!", "success");
    } else {
      showMessage("Error", "Failed to add seance: " + result.error, "error");
    }
  } catch (error) {
    console.error("Error adding seance:", error);
    showMessage("Error", "Error adding seance: " + error, "error");
  }
}

// Global variables for edit modal
let currentEditSeanceDate = null;
let currentEditSeanceIndex = null;
let currentEditTeachers = [];
let currentEditRooms = [];

async function editSeance(date, index) {
  currentEditSeanceDate = date;
  currentEditSeanceIndex = index;

  const seance = seancesData[date][index];

  // Convert time format from HH:MM:SS to HH:MM for input field
  const startTime = seance.h_debut.substring(0, 5);
  const endTime = seance.h_fin.substring(0, 5);

  // Set the time values
  $("#editSeanceStartTime").val(startTime);
  $("#editSeanceEndTime").val(endTime);

  // Initialize arrays with current data
  currentEditTeachers = [...seance.enseignants];
  currentEditRooms = [...seance.salles];

  // Display current teachers and rooms
  displayEditTeachers();
  displayEditRooms();

  // Update modal title
  $("#editSeanceModalLabel").text(`Edit ${seance.name} for ${date}`);

  // Show the modal
  $("#editSeanceModal").modal("show");
}

function addEditTeacher() {
  const input = $("#editTeacherInput");
  const teacherCode = input.val().trim();

  if (!teacherCode) {
    showMessage("Error", "Please enter a teacher code", "error");
    return;
  }

  // Validate that it's a number
  if (!/^\d+$/.test(teacherCode)) {
    showMessage("Error", "Teacher code must be a number", "error");
    return;
  }

  const teacherNum = parseInt(teacherCode);

  // Check if teacher already exists
  if (currentEditTeachers.includes(teacherNum)) {
    showMessage("Warning", "Teacher already added", "warning");
    return;
  }

  // Add teacher to array and display
  currentEditTeachers.push(teacherNum);
  displayEditTeachers();
  input.val("");
}

function addEditRoom() {
  const input = $("#editRoomInput");
  const roomCode = input.val().trim();

  if (!roomCode) {
    showMessage("Error", "Please enter a room code", "error");
    return;
  }

  // Check if room already exists
  if (currentEditRooms.includes(roomCode)) {
    showMessage("Warning", "Room already added", "warning");
    return;
  }

  // Add room to array and display
  currentEditRooms.push(roomCode);
  displayEditRooms();
  input.val("");
}

function displayEditTeachers() {
  const container = $("#editTeachersContainer");
  container.empty();

  if (currentEditTeachers.length === 0) {
    container.append('<p class="text-muted">No teachers added</p>');
    return;
  }

  currentEditTeachers.forEach((teacher) => {
    const badge = $(`
            <span class="badge badge-info mr-2 mb-2" style="font-size: 0.9rem;">
              ${teacher}
              <button type="button" class="btn btn-sm ml-1" style="color: white; background: none; border: none; padding: 0;" onclick="removeEditTeacher(${teacher})">
                <i class="fas fa-times"></i>
              </button>
            </span>
          `);
    container.append(badge);
  });
}

function displayEditRooms() {
  const container = $("#editRoomsContainer");
  container.empty();

  if (currentEditRooms.length === 0) {
    container.append('<p class="text-muted">No rooms added</p>');
    return;
  }

  currentEditRooms.forEach((room) => {
    const badge = $(`
            <span class="badge badge-success mr-2 mb-2" style="font-size: 0.9rem;">
              ${room}
              <button type="button" class="btn btn-sm ml-1" style="color: white; background: none; border: none; padding: 0;" onclick="removeEditRoom('${room}')">
                <i class="fas fa-times"></i>
              </button>
            </span>
          `);
    container.append(badge);
  });
}

function removeEditTeacher(teacherCode) {
  currentEditTeachers = currentEditTeachers.filter((t) => t !== teacherCode);
  displayEditTeachers();
}

function removeEditRoom(roomCode) {
  currentEditRooms = currentEditRooms.filter((r) => r !== roomCode);
  displayEditRooms();
}

// Allow adding teachers/rooms with Enter key in edit modal
$(document).ready(function () {
  $("#editTeacherInput").keypress(function (e) {
    if (e.which === 13) {
      // Enter key
      addEditTeacher();
    }
  });

  $("#editRoomInput").keypress(function (e) {
    if (e.which === 13) {
      // Enter key
      addEditRoom();
    }
  });
});

async function saveEditSeance() {
  const startTime = $("#editSeanceStartTime").val();
  const endTime = $("#editSeanceEndTime").val();

  if (!startTime || !endTime) {
    showMessage("Error", "Please enter both start and end times", "error");
    return;
  }

  // Convert time format from HH:MM to HH:MM:SS
  const h_debut = startTime + ":00";
  const h_fin = endTime + ":00";

  try {
    const result = await eel.update_seance(
      currentEditSeanceDate,
      currentEditSeanceIndex,
      h_debut,
      h_fin,
      currentEditRooms,
      currentEditTeachers,
    )();

    if (result.success) {
      $("#editSeanceModal").modal("hide");
      await loadSeancesForDate(currentEditSeanceDate);
      showMessage("Success", "Seance updated successfully!", "success");
    } else {
      showMessage("Error", "Failed to update seance: " + result.error, "error");
    }
  } catch (error) {
    console.error("Error updating seance:", error);
    showMessage("Error", "Error updating seance: " + error, "error");
  }
}

async function deleteSeance(date, index) {
  showConfirmation(
    "Delete Seance",
    "Are you sure you want to delete this seance?",
    async function () {
      try {
        const result = await eel.delete_seance(date, index)();
        if (result.success) {
          await loadSeancesForDate(date);
          showMessage("Success", "Seance deleted successfully!", "success");
        } else {
          showMessage(
            "Error",
            "Failed to delete seance: " + result.error,
            "error",
          );
        }
      } catch (error) {
        console.error("Error deleting seance:", error);
        showMessage("Error", "Error deleting seance: " + error, "error");
      }
    },
  );
}

// Modal helper functions
function showMessage(title, message, type = "info") {
  $("#messageModalLabel").text(title);
  $("#messageModalBody").text(message);

  // Change modal color based on type
  const modal = $("#messageModal .modal-content");
  modal.removeClass("border-success border-danger border-warning");
  if (type === "success") {
    modal.addClass("border-success");
  } else if (type === "error") {
    modal.addClass("border-danger");
  } else if (type === "warning") {
    modal.addClass("border-warning");
  }

  $("#messageModal").modal("show");
}

function showConfirmation(title, message, callback) {
  $("#confirmationModalLabel").text(title);
  $("#confirmationModalBody").text(message);
  confirmationCallback = callback;
  $("#confirmationModal").modal("show");
}

// Handle confirmation modal buttons
$("#confirmationConfirm").click(function () {
  $("#confirmationModal").modal("hide");
  if (confirmationCallback) {
    confirmationCallback();
    confirmationCallback = null;
  }
});

$("#confirmationCancel").click(function () {
  confirmationCallback = null;
});

// Import function - show file dialog
function importSeances() {
  $("#csvFileInput").val(""); // Clear previous selection
  $("#importCsvModal").modal("show");
}

// Process CSV import after file selection
async function processCsvImport() {
  const fileInput = document.getElementById("csvFileInput");
  const file = fileInput.files[0];

  if (!file) {
    showMessage("Error", "Please select a CSV or XLSX file.", "error");
    return;
  }

  const fileName = file.name.toLowerCase();
  if (!fileName.endsWith(".csv") && !fileName.endsWith(".xlsx")) {
    showMessage("Error", "Please select a valid CSV or XLSX file.", "error");
    return;
  }

  try {
    // Read file content based on file type
    let fileContent;
    if (fileName.endsWith(".xlsx")) {
      // Read as binary for XLSX files
      fileContent = await readFileAsBinary(file);
    } else {
      // Read as text for CSV files
      fileContent = await readFileContent(file);
    }

    // Save file to server and import
    const result = await eel.import_seances_from_file_content(fileContent, file.name)();
    $("#importCsvModal").modal("hide");

    if (result.success) {
      showMessage(
        "Success",
        `Data imported successfully! ${result.seances_info.total_sessions} sessions loaded.`,
        "success",
      );

      // Update the UI with imported data
      selectedDates = result.seances_info.dates || [];

      // Sort dates before displaying
      selectedDates.sort((a, b) => {
        const dateA = new Date(a.split("/").reverse().join("-"));
        const dateB = new Date(b.split("/").reverse().join("-"));
        return dateA - dateB;
      });

      // Refresh calendar to show imported dates
      renderCalendar();

      // Clear existing tables
      $("#seancesContainer").empty();
      seancesData = {};

      // Load seances for each imported date in sorted order
      for (const date of selectedDates) {
        await loadSeancesForDate(date);
      }
    } else {
      showMessage("Error", "Failed to import data: " + result.error, "error");
    }
  } catch (error) {
    console.error("Error importing data:", error);
    showMessage("Error", "Error importing data: " + error, "error");
  }
}

// Helper function to read file content as text
function readFileContent(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = function (e) {
      resolve(e.target.result);
    };
    reader.onerror = function () {
      reject(new Error("Failed to read file"));
    };
    reader.readAsText(file);
  });
}

// Helper function to read file content as binary (for XLSX files)
function readFileAsBinary(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = function (e) {
      // Convert ArrayBuffer to base64 string
      const bytes = new Uint8Array(e.target.result);
      let binary = '';
      const len = bytes.byteLength;
      for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      resolve(btoa(binary));
    };
    reader.onerror = function () {
      reject(new Error("Failed to read file"));
    };
    reader.readAsArrayBuffer(file);
  });
}

// Clear all seances function
async function clearAllSeances() {
  showConfirmation(
    "Clear All Data",
    "Are you sure you want to delete all seances and souhaits? This action cannot be undone.",
    async function () {
      try {
        const result = await eel.clear_all_seances()();
        if (result.success) {
          // Clear UI data
          selectedDates = [];
          seancesData = {};
          
          // Clear seances container
          $("#seancesContainer").empty();
          
          // Refresh calendar to remove selected dates
          renderCalendar();
          
          // Reset date selection UI
          $("#selectedDateInfo").hide();
          $("#selectDateBtn").prop("disabled", true);
          $("#showSeancesBtn").hide();
          $("#removeDateBtn").hide();
          
          // Remove clicked date styling
          $(".calendar-day").removeClass("clicked-date");
          clickedCalendarDate = null;
          
          showMessage("Success", "All seances and souhaits have been cleared successfully!", "success");
        } else {
          showMessage("Error", "Failed to clear data: " + result.error, "error");
        }
      } catch (error) {
        console.error("Error clearing seances:", error);
        showMessage("Error", "Error clearing seances: " + error, "error");
      }
    }
  );
}

// Navigation functions
function navigateToEnseignants() {
  window.location.href = "/enseignants.html";
}
