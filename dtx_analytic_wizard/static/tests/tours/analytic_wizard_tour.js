/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("test_analytic_distribution_assign_tour", {
    test: true,
    steps: () => [
        {
            trigger: '.o_data_row:first .o_data_cell',
            content: "Open the first purchase order",
            run: "click",
        },
        {
            trigger: '.o_form_view .o_field_widget[name="order_line"]',
            content: "Wait for form to fully load",
        },
        {
            trigger: '.o_cp_action_menus .dropdown-toggle',
            content: "Open the cog/actions menu",
            run: "click",
        },
        {
            trigger: 'span:contains("Assign Analytic Accounts")',
            content: "Click Assign Analytic Accounts",
            run: "click",
        },
        {
            trigger: '.modal',
            content: "Verify the wizard dialog opened",
        },
        {
            trigger: '.modal footer .btn-primary',
            content: "Click Apply button",
            run: "click",
        },
        {
            trigger: '.o_form_view .o_field_widget[name="order_line"]',
            content: "Verify we are back on the purchase order form",
        },
    ],
});

registry.category("web_tour.tours").add("test_analytic_distribution_remove_tour", {
    test: true,
    steps: () => [
        {
            trigger: '.o_data_row:first .o_data_cell',
            content: "Open the first purchase order",
            run: "click",
        },
        {
            trigger: '.o_form_view .o_field_widget[name="order_line"]',
            content: "Wait for form to fully load",
        },
        {
            trigger: '.o_cp_action_menus .dropdown-toggle',
            content: "Open the cog/actions menu",
            run: "click",
        },
        {
            trigger: 'span:contains("Remove Analytic Accounts")',
            content: "Click Remove Analytic Accounts",
            run: "click",
        },
        {
            trigger: '.modal',
            content: "Verify the remove wizard dialog opened",
        },
        {
            trigger: '.modal .o_field_widget[name="remove_all"] input, .modal input[id*="remove_all"], .modal .form-check-input',
            content: "Check Remove All checkbox",
            run: "click",
        },
        {
            trigger: '.modal footer .btn-danger',
            content: "Click Remove button",
            run: "click",
        },
        {
            trigger: '.o_form_view .o_field_widget[name="order_line"]',
            content: "Verify we are back on the purchase order form",
        },
    ],
});
