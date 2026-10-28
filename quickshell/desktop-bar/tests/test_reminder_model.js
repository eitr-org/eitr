const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../ReminderModel.js'), 'utf8').replace('.pragma library', ''), context);
assert.equal(context.parse('bad').length, 0);
assert.equal(context.parse('{}').length, 0);
const day = new Date(2026, 9, 30, 9);
const text = JSON.stringify([{id:'1', text:'Dentist', due:day.getTime()/1000}, {id:'2', text:'Other', due:day.getTime()/1000+86400}, {id:'3', text:'invalid', due:'bad'}]);
assert.equal(context.parse(text).length, 2);
assert.equal(context.forDay(context.parse(text), day)[0].text, 'Dentist');
assert.equal(context.forDay(context.parse('[]'), day).length, 0);
const qml = fs.readFileSync(path.join(__dirname, '../CalendarMenu.qml'), 'utf8');
assert.match(qml, /watchChanges: true/);
assert.match(qml, /onFileChanged: reload\(\)/);
assert.match(qml, /menu\.updateContent\(function\(\) \{ menu\.applySnapshot\("reminders", ReminderModel\.parse\(snapshot\)\)/);
console.log('Reminder model passed');
const anchor = new Date(2028, 0, 31, 8);
const series = {id:'r', text:'Monthly', due:anchor.getTime()/1000, repeat_anchor:'2028-01-31T08:00:00', repeat_index:0, repeat:{frequency:'monthly', count:3}};
assert.equal(context.forDay([series], new Date(2028, 1, 29)).length, 1);
assert.equal(context.forDay([series], new Date(2028, 2, 31))[0].due, new Date(2028, 2, 31, 8).getTime()/1000);
assert.equal(context.forMonth([series], 2028, 3).length, 0);
series.repeat = {frequency:'weekly', weekdays:[0,3], until:'2028-02-10'};
series.repeat_anchor = '2028-01-31T08:00:00';
assert.equal(context.forMonth([series], 2028, 1).length, 3);
series.repeat_index = 3;
assert.equal(context.forMonth([series], 2028, 1).length, 1);
// Expanded occurrences carry their index, so the calendar can tell the pending one apart.
const weekly = {id:'w', text:'Weekly', due:new Date(2028, 0, 3, 9).getTime()/1000, repeat_anchor:'2028-01-03T09:00:00', repeat_index:0, repeat:{frequency:'weekly'}};
assert.deepEqual(Array.from(context.forMonth([weekly], 2028, 0), (item) => item.occurrence), [0, 1, 2, 3, 4]);
assert.equal(context.forDay([{id:'o', text:'Once', due:day.getTime()/1000}], day)[0].occurrence, undefined);
assert.match(qml, /Qt\.Key_Escape && menu\.pendingKey !== ""\) menu\.cancelDelete\(\)/);
assert.match(qml, /\["python3", reminderHelper, "cancel", identifier, scope\]/);
assert.match(qml, /Eitr\.Paths\.code\("walker\/scripts\/actions\/tools\/reminders\.py"\)/);
// Subscribed calendar events: all-day ones cover [date, endDate); timed ones every day they overlap.
const at = (date, hour, minute) => new Date(2026, 9, date, hour, minute || 0).getTime() / 1000;
const events = context.parseEvents(JSON.stringify({events: [
    {key:'night', calendar:'Work', title:'Night shift', start:at(29, 22), end:at(30, 6)},
    {key:'trip', calendar:'Home', title:'Trip', allDay:true, date:'2026-10-30', endDate:'2026-11-01'},
    {key:'bad', calendar:'Work', title:'No times'}, {key:'bad-day', calendar:'Work', title:'x', allDay:true, date:'soon', endDate:'later'}]}));
assert.deepEqual(Array.from(events, (item) => item.key), ['night', 'trip']);
assert.equal(context.parseEvents('nonsense').length, 0);
assert.deepEqual(Array.from(context.eventsForDay(events, new Date(2026, 9, 31)), (item) => item.key), ['trip']);
assert.deepEqual(Array.from(context.eventsForDay(events, new Date(2026, 10, 1)), (item) => item.key), []);
const items = context.dayItems([{id:'r', text:'Dentist', due:at(30, 5)}], events, new Date(2026, 9, 30));
assert.deepEqual(Array.from(items, (item) => [item.kind, item.id, !!item.continued]),
    [['event', 'trip', false], ['event', 'night', true], ['reminder', 'r', false]]);
assert.match(qml, /menu\.updateContent\(function\(\) \{ menu\.applySnapshot\("events", ReminderModel\.parseEvents\(snapshot\)\)/);
assert.match(qml, /"\/eitr\/calendar-events.json"/);
