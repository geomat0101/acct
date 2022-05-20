var app;
app = angular.module('acctApp', ['ngRoute', 'ui.date']);

app.config(['$routeProvider',
    function ($routeProvider) {
        $routeProvider.
            when('/', {
                controller: 'acctListCtl',
                templateUrl: 'acct.html'
            }).
            when('/acct/:acctType/:acctName/:viewType', {
                controller: 'acctListCtl',
                templateUrl: 'acct.html'
            }).
            when('/xact', {
                controller: 'acctListCtl',
                templateUrl: 'xact.html'
            }).
            when('/import', {
                controller: 'importCtl',
                templateUrl: 'import.html'
            }).
            when('/income', {
                templateUrl: 'income.html'
            }).
            when('/balance', {
                templateUrl: 'balance.html'
            }).
            when('/charts', {
                templateUrl: 'charts.html'
            }).
            when('/budgets', {
                templateUrl: 'budgets.html'
            }).
            when('/help/:helpTopic', {
                controller: 'helpCtl',
                templateUrl: 'help.html'
            }).
            when('/help', {
                redirectTo: '/help/tutorial'
            }).
            when('/login', {
                controller: 'loginCtl',
                templateUrl: 'login.html'
            }).
            otherwise({
                redirectTo: '/'
            });
    }]);

app.factory('acctListFactory', function ($http) {
    return {
        getAcctList: function () {
            return $http.get('/acctapi?method=load_acctlist')
                .then(function (result) {
                    return result.data;
                });
        },
        getAcctDebits: function (atype, acctName) {
            var url;
            url = '/acctapi?method=get_xact_data&args=' + atype +
            '&args=' + acctName +
            '&args=false' +
            '&args=debit';
            return $http.get(url).then(function (result) {
                return result.data;
            });
        },
        getAcctCredits: function (atype, acctName) {
            var url;
            url = '/acctapi?method=get_xact_data&args=' + atype +
            '&args=' + acctName +
            '&args=false' +
            '&args=credit';
            return $http.get(url).then(function (result) {
                return result.data;
            });
        },
        addXact: function (debitAcctType, debitAcctName, creditAcctType, creditAcctName, amount, description, xactDate) {
            var url;
            url = '/acctapi?method=add_xact&args=' + debitAcctType +
            '&args=' + debitAcctName +
            '&args=' + creditAcctType +
            '&args=' + creditAcctName +
            '&args=' + amount +
            '&args=' + description +
            '&args=' + xactDate;
            return $http.get(url).then(function (result) {
                return result.data;
            });
        },
        addAcct: function (acctType, acctName) {
            var url;
            url = '/acctapi?method=add_acct&args=' + acctType +
            '&args=' + acctName;
            return $http.get(url).then(function (result) {
                return result.data;
            });
        }
    }
});

app.controller('acctListCtl', ['$scope', '$q', '$routeParams', 'acctListFactory', function ($scope, $q, $routeParams, acctListFactory) {
    $scope.creditTotal = '';
    $scope.debitTotal = '';
    $scope.acctName = '[ None ]';
    $scope.xactDate = new Date();

    $scope.acctDetail = function (atype, acctName, create, xtype) {
        $scope.acctType = atype;
        $scope.acctName = acctName;
        $q.all([
            acctListFactory.getAcctDebits(atype, acctName).then(function (result) {
                $scope.debitTotal = Number(result[0]).toFixed(2);
                $scope.debitData = result[1];
            }),
            acctListFactory.getAcctCredits(atype, acctName).then(function (result) {
                $scope.creditTotal = Number(result[0]).toFixed(2);
                $scope.creditData = result[1];
            })
        ]).then(function () {
            if (['ASSET', 'EXPENSE'].includes($scope.acctType))
            {
                var invertedCredits = [];
                for (var idx in $scope.creditData) {
                    var record = $scope.creditData[idx];
                    var recordCopy = record.slice(0);
                    recordCopy[1] = (Number(record[1]) * -1).toFixed(2);
                    invertedCredits[invertedCredits.length] = recordCopy;
                }

                $scope.combinedData = $scope.debitData.concat(invertedCredits)
                    .sort(function (a, b) {
                        // by date, descending, then by id desc
                        if (b[2] == a[2]) {
                            return b[0] - a[0];
                        }
                        return b[2] - a[2];
                    });
            } else {
                var invertedDebits = [];
                for (var idx in $scope.debitData) {
                    var record = $scope.debitData[idx];
                    var recordCopy = record.slice(0);
                    recordCopy[1] = (Number(record[1]) * -1).toFixed(2);
                    invertedDebits[invertedDebits.length] = recordCopy;
                }

                $scope.combinedData = $scope.creditData.concat(invertedDebits)
                    .sort(function (a, b) {
                        // by date, descending, then by id desc
                        if (b[2] == a[2]) {
                            return b[0] - a[0];
                        }
                        return b[2] - a[2];
                    });
            }
            var subtotal = 0;
            for (var i = $scope.combinedData.length - 1; i >= 0; i--) {
                record = $scope.combinedData[i];
                // lots of type casting this way, but we want to store the value
                // from each cycle as a properly formatted currency value, and
                // this ultimately will help reduce precision errors in the subtotal
                subtotal = (Number(subtotal) + Number(record[1])).toFixed(2);
                record[record.length] = subtotal;
            }
        });
    };

    $scope.loadAcctList = function () {
        acctListFactory.getAcctList().then(function (result) {
            $scope.acctList = result.acctlist;
            $scope.totalDebits = result.total_debits;
            $scope.totalCredits = result.total_credits;
            $scope.loggedIn = result.logged_in;
        });
    };

    $scope.loadAcctList();

    if (typeof($routeParams.acctName) == 'undefined') {
        $scope.viewType = 'combined';
    } else {
        $scope.acctType = $routeParams.acctType;
        $scope.acctName = $routeParams.acctName;
        $scope.viewType = $routeParams.viewType;    // combined, debits, credits
        $scope.acctDetail($routeParams.acctType, $routeParams.acctName);
    }

    $scope.submitAddXact = function () {
        var xactDate = $scope.xactDate;

        if (xactDate instanceof Date) {
            xactDate = xactDate.toLocaleDateString();
        }

        acctListFactory.addXact($scope.debitAcct[0], $scope.debitAcct[1], $scope.creditAcct[0], $scope.creditAcct[1],
            Number($scope.amount).toFixed(2), $scope.description, xactDate)
            .then(function () {
                $scope.loadAcctList();
                $scope.amount = '';
                $scope.description = '';

                // check if one of these accounts is currently loaded as
                // an account detail view and reload that if necessary
                if (($scope.debitAcct[0] == $scope.acctType && $scope.debitAcct[1] == $scope.acctName)
                    || ($scope.creditAcct[0] == $scope.acctType && $scope.creditAcct[1] == $scope.acctName)) {

                    $scope.acctDetail($scope.acctType, $scope.acctName);
                }
            }
        );
    };

    $scope.submitAddAcct = function () {
        var newName = $scope.newAcctName.replace(' ', '_');
        acctListFactory.addAcct($scope.newAcctType, newName)
            .then(function () {
                $scope.loadAcctList();
                $scope.newAcctName = '';
            });
    };

}
]);


app.factory('importFactory', function ($http) {
    return {
        getPatterns: function () {
            var url;
            url = '/acctapi?method=get_qif_patterns';
            return $http.get(url).then(function (result) {
                var currAcct = '';
                var patternMap = Object();
                var idx;
                var record;
                for (idx in result.data) {
                    record = result.data[idx];
                    if (record[1] != currAcct) {
                        currAcct = record[1];
                        patternMap[currAcct] = Array();
                    }
                    patternMap[currAcct][patternMap[currAcct].length] = record;
                }
                return patternMap;
            });
        },
        addPattern: function (acctType, acctName, pattern, cptyAcctType, cptyAcctName) {
            var url;
            url = '/acctapi?method=add_qif_pattern&args=' + acctType +
            '&args=' + acctName +
            '&args=' + pattern +
            '&args=' + cptyAcctType +
            '&args=' + cptyAcctName;
            return $http.get(url).then(function (result) {
                return result.data;
            });
        },
        delPattern: function (acctType, acctName, pattern, cptyAcctType, cptyAcctName) {
            var url;
            url = '/acctapi?method=del_qif_pattern&args=' + acctType +
            '&args=' + acctName +
            '&args=' + pattern +
            '&args=' + cptyAcctType +
            '&args=' + cptyAcctName;
            return $http.get(url).then(function (result) {
                return result.data;
            });
        },
        getPendingImports: function () {
            var url;
            url = '/acctapi?method=get_qif_pending';
            return $http.get(url).then(function (result) {
                return result.data;
            });
        },
        applyPatterns: function () {
            var url;
            url = '/acctapi?method=applyQIFPatterns';
            return $http.get(url).then(function (result) {
                return result.data;
            });
        }
    }
});


app.controller('importCtl', function ($scope, acctListFactory, importFactory) {

    $scope.pendingImports = {'ASSET': [], 'LIABILITY': []};
    $scope.displayAcct = {'ASSET': [], 'LIABILITY': []};

    $scope.loadAcctList = function () {
        acctListFactory.getAcctList().then(function (result) {
            $scope.acctList = result.acctlist;
            $scope.loadPending();
        });
    };
    $scope.loadAcctList();

    $scope.loadPatterns = function () {
        importFactory.getPatterns().then(function (result) {
            $scope.qifPatterns = result;
        });
    };
    $scope.loadPatterns();

    $scope.loadPending = function () {
        importFactory.getPendingImports().then(function (result) {
            for (var i = 0; i < $scope.acctList.length; i++) {
                var acct = $scope.acctList[i];
                if (acct[0] == 'ASSET' || acct[0] == 'LIABILITY') {
                    $scope.pendingImports[acct[0]][acct[1]] = [];
                    $scope.displayAcct[acct[0]][acct[1]] = false;
                }
            }
            for (var xact in result) {
                $scope.pendingImports[result[xact][0]][result[xact][1]].push(result[xact]);
            }
        });
    };

    $scope.toggleDisplay = function (acctType, acctName) {
        $scope.displayAcct[acctType][acctName] = ! $scope.displayAcct[acctType][acctName];
    }

    $scope.addPattern = function (acctType, acctName, pattern, cptyAcctType, cptyAcctName) {
        importFactory.addPattern(acctType, acctName, pattern, cptyAcctType, cptyAcctName).then(
            function () {
                $scope.loadPatterns();
            }
        )
    };

    $scope.delPattern = function (patternRecord) {
        importFactory.delPattern(patternRecord[0], patternRecord[1],
            patternRecord[2], patternRecord[3], patternRecord[4]).then(
            function () {
                $scope.loadPatterns();
            }
        )
    };

    $scope.applyPatterns = function () {
        $scope.nPending = 'Working...';
        importFactory.applyPatterns().then(
            function () {
                $scope.loadPending();
                $scope.loadAcctList();
            }
        )
    };

    $scope.submitAddAcct = function () {
        var newName = $scope.newAcctName.replace(' ', '_');
        acctListFactory.addAcct($scope.newAcctType, newName)
            .then(function () {
                $scope.loadAcctList();
                $scope.newAcctName = '';
            });
    };
})
;


app.factory('loginFactory', function ($http) {
    return {
        login: function (username, password) {
            var url;
            url = '/acctapi?method=auth&username=' + username + '&password=' + password;
            return $http.get(url).then(function (result) {
                return result.data;
            });
        },

        logout: function () {
            var url;
            url = '/acctapi?method=logout';
            return $http.get(url).then(function (result) {
                return result.data;
            });
        },

        changePassword: function (chgPwUsername, chgPwPassword, chgPwNewPass) {
            var url;
            url = '/acctapi?method=change_password&args=' + chgPwUsername +
            '&args=' + chgPwPassword +
            '&args=' + chgPwNewPass;
            return $http.get(url).then(function (result) {
                return result.data;
            });
        },

        createInstance: function (newBBUsername, newBBPassword) {
            var url;
            url = '/acctapi?method=create_instance&args=' + newBBUsername +
            '&args=' + newBBPassword;
            return $http.get(url).then(function (result) {
                return result.data;
            });
        }
    };
});


app.controller('loginCtl', function ($scope, $location, loginFactory) {
    $scope.login = function (username, password) {
        loginFactory.login(username, password).then(
            function (result) {
                if (result == 'false') {
                    alert('Login Failed')
                } else {
                    $location.path("/");
                }
            }
        )
    };

    $scope.logout = function () {
        loginFactory.logout().then(
            function () {
                $location.path("/");
            }
        )
    };

    $scope.changePassword = function (chgPwUsername, chgPwPassword, chgPwNewPass, chgPwNewPassConfirm) {
        if (chgPwNewPass != chgPwNewPassConfirm) {
            alert('Password mismatch');
        } else {
            loginFactory.changePassword(chgPwUsername, chgPwPassword, chgPwNewPass).then(
                function () {
                    $scope.login(chgPwUsername, chgPwNewPass);
                }
            )
        }
    };

    $scope.createInstance = function (newBBUsername, newBBPassword, newBBPassConfirm) {
        if (newBBPassword != newBBPassConfirm) {
            alert('Password mismatch');
        } else {
            loginFactory.createInstance(newBBUsername, newBBPassword).then(
                function (result) {
                    if (result == 'false') {
                        alert('Falied: try a diferent username');
                    } else {
                        $scope.login(newBBUsername, newBBPassword);
                    }
                }
            )
        }
    };
});


app.controller('helpCtl', function ($scope, $routeParams) {
    $scope.helpTopic = $routeParams.helpTopic;
});


