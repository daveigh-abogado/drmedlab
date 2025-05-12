/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */

module.exports = {
    content: [
        /**
         * HTML. Paths to Django template files that will contain Tailwind CSS classes.
         */

        /*  Templates within theme app (<tailwind_app_name>/templates), e.g. base.html. */
        '../templates/**/*.html',

        /*
         * Main templates directory of the project (BASE_DIR/templates).
         * Adjust the following line to match your project structure.
         */
        '../../templates/**/*.html',

        /*
         * Templates in other django apps (BASE_DIR/<any_app_name>/templates).
         * Adjust the following line to match your project structure.
         */
        '../../**/templates/**/*.html',

        /**
         * JS: If you use Tailwind CSS in JavaScript, uncomment the following lines and make sure
         * patterns match your project structure.
         */
        /* JS 1: Ignore any JavaScript in node_modules folder. */
        // '!../../**/node_modules',
        /* JS 2: Process all JavaScript files in the project. */
        // '../../**/*.js',

        /**
         * Python: If you use Tailwind CSS classes in Python, uncomment the following line
         * and make sure the pattern below matches your project structure.
         */
        // '../../**/*.py'
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Roboto', 'system-ui', 'sans-serif'],
                // Add more custom font families as needed
            },
            colors: {
                myblue: {
                    primary: 'rgba(39, 66, 145, 1)',       // For solid buttons
                    secondary: 'rgba(39, 66, 145, 0.12)',  // For cancel buttons
                    highlight: 'rgba(0, 186, 255, 1)', // For highlight
                    borderPrimary: 'rgba(39, 66, 145, 0.6)', // For borders
                },
                complete: {
                    primary: 'rgba(31, 116, 32, 1)',      // Text
                    secondary: 'rgba(31, 116, 32, 0.2)',  // Background
                    borderPrimary: 'rgba(31, 116, 32, 0.4)', // Border
                },
                progress: {
                    primary: 'rgba(234, 193, 12, 1)',      // Text
                    secondary: 'rgba(234, 193, 12, 0.2)',  // Background
                    borderPrimary: 'rgba(234, 193, 12, 0.4)', // Border
                },
                unstarted: {
                    primary: 'rgba(188, 196, 221, 1)',      // Text
                    secondary: '#E9ECF4',  // Background
                    borderPrimary: '#BCC4DD', // Border
                },
            },
        },
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
         * for forms. If you don't like it or have own styling for forms,
         * comment the line below to disable '@tailwindcss/forms'.
         */
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/line-clamp'),
        require('@tailwindcss/aspect-ratio'),
    ],
}
