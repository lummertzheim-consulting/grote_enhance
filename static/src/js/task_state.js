/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

console.log('rpc - =-=- =- =',rpc)

document.addEventListener("click", async function (ev) {
    // Look for the closest element with our class
    const target = ev.target.closest(".change-task-state");

    if (!target) {
        return; // Click was not on a task state item
    }

    ev.preventDefault();
    console.log('Clicked element:', target);

    const taskId = target.dataset.taskId;
    const newState = target.dataset.newState;

    if (!taskId || !newState) {
        console.error("Missing taskId or newState");
        return;
    }

    try {
        // Call Odoo 18 backend controller
        const response = await rpc(`/portal/task/${taskId}/change_state`, {
            new_state: newState,
        });

        console.log("RPC Response:", response);

        if (response.success) {
            window.location.reload();
        } else {
            alert(response.error || "Failed to update task state.");
        }
    } catch (err) {
        console.error("Error updating task state:", err);
        alert("An error occurred while updating the task.");
    }
});
