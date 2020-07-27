{


window.ReviewBot = window.ReviewBot || {};


/**
 * The model for the configuration page.
 *
 * Model Attributes:
 *     brokerURL (string):
 *         The URL for the AMQP broker.
 *
 *     user (number):
 *         The ID of the user for Review Bot to post as.
 */
ReviewBot.ExtensionConfig = Backbone.Model.extend({
    defaults: {
        brokerURL: '',
        user: null,
    },

    /**
     * Initialize the model.
     *
     * Args:
     *     attributes (object):
     *         Initial attribute values for the model.
     *
     *     options (object):
     *         Additional options for the model.
     *
     * Option Args:
     *     integrationConfigURL (string):
     *         The URL of the integration list page.
     *
     *     userConfigURL (string):
     *         The URL of the user configuration endpoint.
     *
     *     workerStatusURL (string):
     *         The URL of the worker status endpoint.
     */
    initialize(attributes, options) {
        Backbone.Model.prototype.initialize.call(this, attributes, options);
        this.options = options;
    },
});


/**
 * A view for configuring the Review Bot user.
 */
const UserConfigView = Backbone.View.extend({
    className: 'rb-c-form-row',

    id: 'reviewbot-user',

    events: {
        'click #reviewbot-user-create': '_createUser',
    },

    _templateRB4: _.template(dedent`
        <div class="rb-c-form-field -is-required">
         <label class="rb-c-form-field__label" for="reviewbot-user-field"><%- labelText %></label>

         <div class="rb-c-form-field__input">
          <select class="related-object-options reviewbot-user-select"
                  name="reviewbot_user"
                  placeholder="<%- selectPlaceholderText %>"
                  id="reviewbot-user-field"></select>
          <span class="reviewbot-user-create-details">
           <% if (!hasUser) { %><%= orHTML %><% } %>
          </span>
          <div class="rb-c-form-field__help"><%- descriptionText %></div>
         </div>
        </div>
    `),

    _templateRB3: _.template(dedent`
        <div class="form-row">
         <label class="required" for="reviewbot-user-field"><%- labelText %></label>
         <select class="related-object-options reviewbot-user-select"
                 name="reviewbot_user"
                 placeholder="<%- selectPlaceholderText %>"
                 id="reviewbot-user-field"></select>
         <span class="reviewbot-user-create-details">
          <% if (!hasUser) { %><%= orHTML %><% } %>
         </span>
         <p class="help"><%- descriptionText %></p>
        </div>
    `),

    _optionTemplate: _.template(dedent`
        <div>
        <% if (avatarURL) { %>
         <img src="<%- avatarURL %>">
        <% } %>
        <% if (fullname) { %>
         <span class="title"><%- fullname %></span>
         <span class="description">(<%- username %>)</span>
        <% } else { %>
         <span class="title"><%- username %></span>
        <% } %>
        </div>
    `),

    /**
     * Render the view.
     *
     * Returns:
     *     UserConfigView:
     *     This object, for chaining.
     */
    render() {
        const user = this.model.get('user');
        const template = RB.Product ? this._templateRB4 : this._templateRB3;

        this.$el.html(template({
            titleText: gettext('Review Bot User'),
            labelText: gettext('Review Bot User:'),
            descriptionText: gettext('Review Bot will use this user account to post reviews.'),
            selectPlaceholderText: gettext('Select an existing user account'),
            orHTML: gettext('or <a href="#" id="reviewbot-user-create">create a new user for Review Bot</a>.'),
            hasUser: (user !== null),
        }));

        const currentItems = [];
        const currentOptions = [];

        if (user !== null) {
            currentItems.push(user.id);
            currentOptions.push(user);
        }

        this._$select = this.$('select');

        this._$select.selectize({
            closeAfterSelect: true,
            dropdownParent: 'body',
            hideSelected: true,
            maxItems: 1,
            preload: 'focus',
            items: currentItems,
            options: currentOptions,
            searchField: ['fullname', 'username'],
            valueField: 'id',
            load: (query, callback) => {
                const params = {
                    fullname: 1,
                    'only-fields': 'avatar_url,fullname,id,username',
                    'only-links': '',
                };

                if (query.length !== 0) {
                    params.q = query;
                }

                $.ajax({
                    type: 'GET',
                    url: SITE_ROOT + 'api/users/',
                    data: params,
                    success: result => callback(result.users),
                    error: (xhr, textStatus, errorThrown) => {
                        alert('Unexpected error when querying for users: ' +
                              errorThrown);
                        console.error('User query failed', xhr, textStatus,
                                      errorThrown);
                        callback();
                    },
                });
            },
            render: {
                item: item => this._optionTemplate({
                    avatarURL: item.avatar_url,
                    id: item.id,
                    fullname: item.fullname,
                    username: item.username,
                }),
                option: item => this._optionTemplate({
                    avatarURL: item.avatar_url,
                    id: item.id,
                    fullname: item.fullname,
                    username: item.username,
                }),
            },
        });

        this._selectize = this._$select[0].selectize;

        this.listenTo(this.model, 'change:user', (model, value) => {
            this._setOption(value);
        });

        return this;
    },

    /**
     * Create a new user.
     *
     * Args:
     *     e (Event):
     *         The event which triggered the action.
     */
    _createUser(e) {
        e.preventDefault();
        e.stopPropagation();

        const $details = this.$('.reviewbot-user-create-details');
        this._selectize.lock();
        $details.html('<span class="fa fa-spinner fa-pulse">');

        $.ajax({
            type: 'POST',
            url: this.model.options.userConfigURL,
            complete: () => {
                this._selectize.unlock();
                this._selectize.blur();
                $details.empty();
            },
            success: result => {
                this._setOption(result);
            },
            error: (xhr, textStatus, errorThrown) => {
                alert('Unexpected error when creating the user: ' +
                      errorThrown);
                console.error('Failed to update user', xhr, textStatus,
                              errorThrown);
            },
        });
    },

    /**
     * Set the currently selected option.
     *
     * Args:
     *     user (object):
     *          The user details.
     */
    _setOption(user) {
        this._selectize.clear(true);
        this._selectize.clearOptions();
        this._selectize.addOption(user);
        this._selectize.setValue(user.id, true);
    },
});


/**
 * A view to show the current broker status.
 */
const BrokerStatusView = Backbone.View.extend({
    events: {
        'click #reviewbot-broker-status-refresh': '_onRefreshClicked',
    },

    _updatingTemplate: _.template(dedent`
        <span class="fa fa-spinner fa-pulse"></span>
        <%- refreshingText %>
    `),

    _connectedTemplate: _.template(dedent`
        <div>
         <span class="fa fa-check"></span>
         <%- connectedText %>
        </div>
        <% if (workers.length === 0) { %>
         <div>
          <span class="fa fa-exclamation-triangle"></span>
          <%- workersText %>
         </div>
        <% } else { %>
         <div>
          <span class="fa fa-check"></span>
          <%- workersText %>
          <ul>
           <% _.each(workers, function(worker) { %>
            <li>
             <span class="fa fa-desktop"></span>
             <%- worker.hostname %>
            </li>
           <% }); %>
          </ul>
         </div>
         <div>
          <span class="fa fa-cogs"></span>
          <%- readyText %>
          <%= configureIntegrationsHTML %>
         </div>
        <% } %>
        <div>
         <a href="#" id="reviewbot-broker-status-refresh"><%- refreshText %></a>
        </div>
    `),

    _errorTemplate: _.template(dedent`
        <div>
         <span class="fa fa-exclamation-triangle"></span>
         <%- errorText %>
        </div>
        <div>
         <a href="#" id="reviewbot-broker-status-refresh"><%- refreshText %></a>
        </div>
    `),

    /**
     * Initialize the view.
     */
    initialize() {
        this._updating = false;
        this._connected = false;
        this._rendered = false;
        this._errorText = '';
        this._workers = [];

        this.listenTo(this.model, 'change', this._update);
        this._update();
    },

    /**
     * Render the view.
     *
     * Returns:
     *     BrokerStatusView:
     *     This object, for chaining.
     */
    render() {
        this._$content = $('<div class="form-row">')
            .appendTo(this.$el);

        this._rendered = true;

        this._updateDisplay();

        return this;
    },

    /**
     * Update the displayed status.
     */
    _updateDisplay() {
        if (!this._rendered) {
            return;
        }

        if (this._updating) {
            this._$content.html(this._updatingTemplate({
                refreshingText: gettext('Checking broker...'),
            }));
        } else if (this._connected) {
            let workersText;

            if (this._workers.length === 0) {
                workersText = gettext('No worker nodes found.');
            } else {
                workersText = interpolate(
                    ngettext('%s worker node:',
                             '%s worker nodes:',
                             this._workers.length),
                    [this._workers.length]);
            }

            this._$content.html(this._connectedTemplate({
                connectedText: gettext('Connected to broker.'),
                workersText: workersText,
                refreshText: gettext('Refresh'),
                workers: this._workers,
                readyText: gettext('Review Bot is ready!'),
                configureIntegrationsHTML: interpolate(
                    gettext('To configure when Review Bot tools are run, set up <a href="%s">integration configurations</a>.'),
                    [this.model.options.integrationConfigURL]),
            }));
        } else {
            this._$content.html(this._errorTemplate({
                errorText: this._errorText,
                refreshText: gettext('Refresh'),
            }));
        }
    },

    /**
     * Handler for when the "Refresh" link is clicked.
     *
     * Args:
     *     e (Event):
     *         The event which triggered the action.
     */
    _onRefreshClicked(e) {
        e.preventDefault();
        e.stopPropagation();

        this._update();
    },

    /**
     * Request status from the server and update the UI.
     */
    _update() {
        if (this._updating) {
            return;
        }

        this._updating = true;
        this._updateDisplay();

        $.ajax({
            type: 'GET',
            url: this.model.options.workerStatusURL,
            success: result => {
                this._workers = result.hosts || [];
                this._connected = (result.state === 'success');
                this._errorText = result.error || '';
                this._updating = false;
                this._updateDisplay();
            },
            error: (xhr, textStatus, errorThrown) => {
                console.error('Failed to get broker status', xhr, textStatus,
                              errorThrown);
                this._errorText = gettext('Unable to connect to broker.');
                this._workers = [];
                this._connected = false;
                this._updating = false;
                this._updateDisplay();
            },
        });
    },
});


/**
 * A view for configuring the broker URL.
 */
const BrokerConfigView = Backbone.View.extend({
    id: 'reviewbot-broker',

    className: 'rb-c-form-row',

    _templateRB4: _.template(dedent`
        <div class="rb-c-form-field -is-required">
         <label class="rb-c-form-field__label" for="reviewbot-broker-field"><%- labelText %></label>

         <div class="rb-c-form-field__input">
          <input id="reviewbot-broker-field" name="reviewbot_broker_url"
                 type="text" value="<%- brokerURL %>">
          <div class="rb-c-form-field__help"><%- descriptionText %></div>
         </div>
        </div>
    `),

    _templateRB3: _.template(dedent`
        <div class="form-row">
         <label class="required" for="reviewbot-broker-field"><%- labelText %></label>
         <input id="reviewbot-broker-field" name="reviewbot_broker_url"
                type="text" value="<%- brokerURL %>">
         <p class="help"><%- descriptionText %></p>
        </div>
    `),

    /**
     * Render the view.
     *
     * Returns:
     *     BrokerConfigView:
     *     This object, for chaining.
     */
    render() {
        const template = RB.Product ? this._templateRB4 : this._templateRB3;

        this.$el.html(template({
            titleText: gettext('Broker'),
            labelText: gettext('Broker URL:'),
            descriptionText: gettext('The URL to your AMQP broker.'),
            brokerURL: this.model.get('brokerURL'),
        }));

        return this;
    }
});


/**
 * A view containing the entire Review Bot extension configuration.
 */
const ConfigView = Backbone.View.extend({
    events: {
        'click input[type="submit"]': '_onSaveClicked',
    },

    _templateRB4: dedent`
        <form class="rb-c-form -is-aligned">
         <fieldset class="rb-c-form-fieldset">
          <div class="rb-c-form-fieldset__content">
           <div class="rb-c-form-fieldset__fields">
           </div>
          </div>
         </fieldset>
         <div class="rb-c-form__actions">
          <div class="rb-c-form__actions-primary">
           <input type="submit" class="rb-c-form__action -is-primary">
          </div>
         </div>
        </form>
    `,

    _templateRB3: dedent`
        <form class="rb-c-form-fieldset__fields">
        </form>
        <div class="submit-row">
         <input type="submit" class="rb-c-form-action -is-primary default">
        </div>
    `,

    /**
     * Initialize the view.
     */
    initialize() {
        this._userConfigView = new UserConfigView({
            model: this.model,
        });

        this._brokerConfigView = new BrokerConfigView({
            model: this.model,
        });
    },

    /**
     * Render the view.
     *
     * Returns:
     *     ConfigView:
     *     This object, for chaining.
     */
    render() {
        this._userConfigView.render();
        this._brokerConfigView.render();

        const template = RB.Product ? this._templateRB4 : this._templateRB3;
        this.$el.html(template);

        this._$form = this.$('form');

        this.$('.rb-c-form-fieldset__fields')
            .append(this._userConfigView.$el)
            .append(this._brokerConfigView.$el);

        this._$saveButton = this.$('input[type="submit"]')
            .val(gettext('Save'));

        return this;
    },

    /**
     * Callback for when the "Save" button is clicked.
     *
     * This saves the form and updates the model.
     */
    _onSaveClicked(e) {
        e.preventDefault();
        e.stopPropagation();

        this._$saveButton.prop('disabled', true);

        const $spinner = $('<span class="fa fa-spinner fa-pulse">')
            .insertBefore(this._$saveButton);

        $.ajax({
            type: 'POST',
            url: window.location.pathname,
            data: this._$form.serialize(),
            complete: () => {
                this._$saveButton.prop('disabled', false);
                $spinner.remove();
            },
            success: response => {
                if (response.result === 'success') {
                    if (response.broker_url) {
                        this.model.set('brokerURL', response.broker_url);
                    }

                    if (response.user) {
                        this.model.set('user', response.user);
                    }
                } else if (response.result === 'error') {
                    console.error('Failed to save Review Bot configuration',
                                  response);
                    alert(response.error);
                } else {
                    console.error('Unexpected response from server when ' +
                                  'saving Review Bot configuration.',
                                  response);
                }
            },
            error: (xhr, textStatus, errorThrown) => {
                alert('Unexpected error when querying broker: ' +
                      errorThrown);
                console.error('Failed to update broker', xhr, textStatus,
                              errorThrown);
            },
        });
    },
});


/**
 * A view containing the extension config and broker status.
 */
ReviewBot.ExtensionConfigView = Backbone.View.extend({
    _templateRB4: _.template(dedent`
        <header class="rb-c-content-header -is-main">
         <h1 class="rb-c-content-header__title"><%- configureText %></h1>
        </header>
        <div class="rb-c-page-content-box -is-content-flush"
	        id="reviewbot-extension-config"></div>

        <header class="rb-c-content-header -is-main">
         <h1 class="rb-c-content-header__title"><%- brokerText %></h1>
        </header>
        <div class="rb-c-page-content-box" id="reviewbot-broker-status"></div>
    `),

    _templateRB3: _.template(dedent`
        <h1 class="title"><%- configureText %></h1>
        <div id="content-main">
         <fieldset class="module aligned" id="reviewbot-extension-config"></fieldset>

         <fieldset class="module aligned" id="reviewbot-broker-status">
          <h2><%- brokerText %></h2>
         </div>
        </fieldset>
    `),

    /**
     * Render the view.
     *
     * Returns:
     *     ReviewBot.ExtensionConfigView:
     *     This object, for chaining.
     */
    render() {
        const template = RB.Product ? this._templateRB4 : this._templateRB3;
        this.$el.html(template({
            configureText: gettext('Configure Review Bot'),
            brokerText: gettext('Broker Status'),
        }));

        this._view = new ConfigView({
	    model: this.model,
            el: this.$('#reviewbot-extension-config')
	});
	this._statusView = new BrokerStatusView({
	    model: this.model,
	    el: this.$('#reviewbot-broker-status')
	});

        this._view.render();
        this._statusView.render();

        return this;
    },
});


}
