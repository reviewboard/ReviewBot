module.exports = {
    reporter: function(errors) {
        console.log(JSON.stringify(errors.map(function(result) {
            var error = result.error;

            return {
                column: error.character,
                code: error.code,
                line: error.line,
                msg: error.reason
            };
        })));
    }
};
