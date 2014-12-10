"use strict";

exports = module.exports = function (grunt) {

    grunt.initConfig({
        todo: {
            options: {
                file: "TODO", githubBoxes: true, colophon: false, usePackage: true
            },
            src: ['addons/**/*.py']
        }
    });

    grunt.loadNpmTasks('grunt-todo');

};
