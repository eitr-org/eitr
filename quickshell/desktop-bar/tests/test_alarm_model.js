const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const model = {};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../clock/AlarmModel.js"), "utf8")
    .replace(/^\.pragma library/, ""), model);
const locale = {amText: "AM", pmText: "PM"};
assert.equal(model.displayTime("00:15", true, locale), "12:15 AM");
assert.equal(model.displayTime("12:15", true, locale), "12:15 PM");
assert.equal(model.displayTime("21:40", false, locale), "21:40");
assert.equal(model.parseClock("12:15", true, "am"), "00:15");
assert.equal(model.parseClock("12:15", true, "pm"), "12:15");
assert.equal(model.parseClock("7:30", true, "pm"), "19:30");
assert.equal(model.parseClock("7:30", false), "07:30");
assert.equal(model.parseClock("0:30", true, "am"), "");
assert.equal(model.parseClock("24:00", false), "");
assert.equal(model.parseClock("23:60", false), "");
const earlier = {alarm: {ringUntil: 60}};
const later = {alarm: {ringUntil: 61}};
assert.equal(model.ring([later, earlier], 59000), earlier);
assert.equal(model.ring([later, earlier], 60000), later);
assert.equal(model.ring([later, earlier], 61000), null);

const reminderModel = {};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../ReminderModel.js"), "utf8")
    .replace(/^\.pragma library/, ""), reminderModel);
const mixed = JSON.stringify([{id: "alarm", text: "Morning", due: 15, alarm: {enabled: false}},
    {id: "reminder", text: "Tea", due: 20}]);
assert.equal(reminderModel.parse(mixed).map(item => item.id).join(","), "reminder");
assert.equal(reminderModel.parseAlarms(mixed).map(item => item.id).join(","), "alarm");
