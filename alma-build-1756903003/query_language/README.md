# Sebi Aggregates (SA)

Do today: No
Done?: No
Importance: Imperative

### How providers expose data

SAP (providers) just give you a list of SAOs.

- If too many, they expose SAOs **on-demand** meaning you must send the query up first. Additionally, they expose the SAO types they support so that a client knows when to ask.

SAO (uniquely identified by `type#object_id@source` )

1. Dictionary (Field → Value and Datatype mapping)
2. ID field (the field that is the id)
3. Links (fields that are queries to be executed)
4. Types (All of the types this object is)
5. Source (The source this object is from)
6. Interactions

---

### How it is modeled

1. `type#object_id` → uniquely identifies an object
2. `@source` → describes where it came from
3. `.field` → describes a specific field of an object

- CSAO Combined object `type#object_id@*.*`
- SAO Object `type#object_id@source.*`
- CSAV Combined value `type#object_id@*.field`
- SAV Value `type#object_id@source.field`

All types can be serialized and deserialized into human-readable text without any loss. This is intended to allow piping the output back into the input, or possibly running other bash functions on it like grep or count.

The query engine pings all SAPs to get all their SAOs, and combines them into CSAOs.

Query language syntax. One query deals with just ONE type.

1. `type` → CSAO[]
    1. Is the first keyword. Returns all CSAOs in the system of that type
2. `#object_id`
    1. CSAO[] → CSAO
3. `@source`
    1. CSAO → SAO

1. `*` → SAO[]
    1. Implied (no need to type it), returns everything.
2. Generic filters
    1. Transformations
        1. SAO[] → SAO[]
        2. SAD[] → SAD[]
    2. Options
        1. `:type`
        2. `#object_id`
        3. `@source` 
3. Field selectors `.field`
    1. Transformations (if not link)
        1. SAO[] → SAD[] (drops if not found) **Drops should be grouped by right? Something feels wrong now.**
        2. SAO → SAD (errors if not found)
    2. Transformations (if field is link). It executes it for each SAO, puts results in a list.
        1. If result is SAD or SAD[] → SAD[]
        2. If result is SAO or SAO[] → SAO[]
4. Boolean operators
    1. `.contains(value)` SAD[] → bool
    2. `value = value` Value, Value → bool
        1. If input is `SAD` , will call `.value()`
        2. If input is `SAD[]`, will call `.single()`
    3. `value AND value` bool, bool → bool
    4. `value OR value` bool, bool → bool
5. Grouped filter `.grouped_filter(query, groupings)`
    1. Groups input SAO[] by keys specified in groupings, or :#@ if specified too.
    2. Runs the query for each grouping, then keeps it if it returns true.
6. Default filter `{query}`
    1. **Is syntactic sugar for .grouped_filter(query, :#).** 
    2. SAO[] → SAO[]
    3. The query must return a bool. The query is run on each input SAO as a filter.
        1. e.g. `{@config_intent_master.name=~"ft" AND .exchange.name="XCME"}`
7. Render field selectors `[fields]`
    1. Sets up field filters for rendering, does nothing else
    2. Transformations
        1. SAO → SAO
        2. SAO[] → SAO[]
8. ANY`[0]`
    1. Transformations
        1. SAO[] → SAO
        2. SAD[] → SAD
    2. Errors if more than one input
9. `.singe()`
    1. SAD[] → Value
    2. Errors if multiple different values
10. `.value()` 
    1. SAD → Value
11. Filter operators
    1. `.grouped_lowest(expression, groupings)` 
    2. `.lowest(expression)` → `.grouped_lowest(expression, :#` 
    3. Expects expression to return.a value, or calls `.single()` or `.value()` on it.
12. `.Interaction`
    1. Capital letter indicates user-defined interaction

Rendering

1. SAO[]
    1. A list of `type#object_id@source`
        
        ```haskell
        app#ft_cme_ags_1@config_intent_master
        app#ft_cme_ags_2@config_intent_master
        app#ft_cme_ags_3@config_intent_master
        ```
        
    2. If all have the same `type` and `object_id` , then 
        
        ```haskell
        <ft_cme_ags_1> app
        	#@ name: ft_cme_ags_1
        1@2@ underlyings: <QQQ>, <DIA>, %<IWM>%
        1@2@ desk: sp500
        	3@ state: UP
        
        Sources
         1. @config_intent_master
         2. @config_intent_staging
         3. @shadow
        ```
        
2. SAD[]
    1. Sample:
        
        ```haskell
        .desk
        	app#ft_cme_ags_1@config_intent_master -> sp500
        	app#ft_cme_ags_2@config_intent_master -> sp500
        	app#ft_cme_ags_2@config_intent_staging -> sp500
        ```
        
    2. If all have the same `type` and `object_id`
        
        ```haskell
        .desk <ft_cme_ags_1> app
        	@config_intent_master -> sp500
        	@config_intent_staging -> sp500
        ```
        
3. SAO
    1. Expands:
        
        ```haskell
        <ft_cme_ags_1> app @config_intent_master
        	#name: ft_cme_ags_1
        	underlyings: <QQQ>, <DIA>, <IWM>
        	desk: sp500
        ```
        
4. SAD
    1. Expands
        
        ```haskell
        .desk <ft_cme_ags_1> app @config_intent_master
        	sp500
        ```
        

`type`#`object_id`@`source` → SAO[]

- Returns  `type#object_id@source` for each SAO on each line (only 1 returned)
    
    ```haskell
    $ app#ft_cme_ags_1@config_intent_master
    app#ft_cme_ags_1@config_intent_master
    ```
    

`type`#`object_id`@`source`[0] → SAO

- Returns a single SAO, expanded
    
    ```haskell
    $ app#ft_cme_ags_1@config_intent_master[0]
    <ft_cme_ags_1> (app @config_intent_master)
    	#name: ft_cme_ags_1
    	underlyings: <QQQ>, <DIA>, <IWM>
    	desk: sp500
    ```
    

`type`@`source`  or `type`#`object_id` → SAO[]

- Returns  `type#object_id@source` for each SAO on each line
    
    ```haskell
    $ app@config_intent_master
    app#ft_cme_ags_1@config_intent_master
    app#ft_cme_ags_2@config_intent_master
    app#ft_cme_ags_3@config_intent_master
    // 523 more...
    $ app@ft_cme_ags_1
    app#ft_cme_ags_1@config_intent_master
    app#ft_cme_ags_1@config_intent_staging
    app#ft_cme_ags_1@shadow
    // 523 more...
    ```
    

`type`#`object_id`[0] → CSAO

- Returns a single CSAO, expanded
    
    ```haskell
    $ app#ft_cme_ags_1[0]
    <ft_cme_ags_1> (app)
    1@config_intent_master 2@config_intent_staging 3@shadow
    	#name: ft_cme_ags_1
    	underlyings (1@2@): <QQQ>, <DIA>, %<IWM>%
    	desk (1@2@): sp500
    	state (3@): UP
    ```
    

`type`#`object_id`@`source`.`field`[0]

- Returns a SAD
    
    ```haskell
    $ app#ft_cme_ags_1@config_intent_master[0].desk
    sp500
    ```
    

`type`#`object_id`@`source`.`field`

- Returns SAD[], ofc only one
    
    ```haskell
    $ app#ft_cme_ags_1@config_intent_master.desk
    app#ft_cme_ags_1@config_intent_master.desk -> sp500
    ```
    

`type`#`object_id`@`source`{`filters`}.`interaction`(`params`) → SAO interaction

`type`#`object_id`@`source`{`filters`}[`select`] → SAD[]

`type`#`object_id`@`source`{`filters`}.`select` → SAD

If what you select is a primary key (with . syntax) then it yields another SAD[]

app#ft_cme_ags_1@config_intent_master{exchange=XCME}

:host{apps.name=”ft_cme_ags_1”}[0]

:host{apps.component

# User stories

### MDS → Packet

```haskell
$ MDS = :mds{.down AND .should_be_up}.lowest(.downtime)
$ MDS
<mds_cme_index_1> (app)
1@config_intent_master 2@config_intent_staging 3@shadow
	#name: ft_cme_ags_1
	underlyings (1@2@): <QQQ>, <DIA>, %<IWM>%
	desk (1@2@): sp500
	state (3@): DOWN
	...
$ MDS.last_death.single()
14739813853
$ :packet{.colo=sg AND .arrival.close_to(MDS.last_death)}
bunch of packets
```

Is there a more beautiful way of doing this? MDS should just have a `.packets_around_death` that returns that query! But it needs access to “self” somehow.

```haskell
$ :packet{.colo=sg AND .arrival.close_to(
		:mds{.down AND .should_be_up}.lowest(.downtime).latest_death
	)}
OR
$ :mds{.down AND .should_be_up}.lowest(.downtime).latest_death.packets_around
```

# Config-intent SAP

1. Apps
    1. Two sources: Config-gen and AE Parsers
    2. Both may have opinions over things, usually they agree.
2. Components
    1. One source: Config-gen

## VUIPs

VUI lives in it’s own repo, and has a list of data providers (VUIPs):

1. A provider yields huge amounts of data that’s already commonized into known abstractions. This output is called CommonSystemData.
2. A provider automatically polls the backend to check for updates. It then recomputes and informs the client of updates using a call back, providing the new CommonSystemData.
3. Config-intent: Can generate data provider interfaces for branches. Once you give it a branch, you get a provider. Gets you as much data as possible.
4. Devops-api: Is just one data provider, pings devops1. Gets you as much data as possible.
5. Infra-intent-api: Just one data provider, pings infra-intent. Gets you as much data as possible.
6. Shadow: Just one data provider, pings ae/ endpoints. Gets you as much data as possible.
7. VictoriaMetrics: Just one data provider, polls VM. Has to be configured with metrics.
8. DeltaTable: Just one data provider, polls delta tables. Has to be configured with delta tables.
9. Etc…

Providers run as separate processes, that may have multiple threads for load (e.g. config-intent might have a thread per branch it services). They then expose a common API to POLL. When you POLL, your requirements are kept for a certain amount of time, and will be kept up to date for you. POLL answers “WAIT” if it’s still getting resources for you. Once you stop calling POLL, your requirements are removed and your data will stop getting auto-fetched.

Providers don’t just give you data in a common abstracted form, they also give you app integrations. Mostly these are just links to other apps (e.g. grafana) for a specific abstraction (e.g. app). But they could be richer iframe panels, etc… Integrations can also be endpoints to DO things. For example, the config-intent provider has an integration to move threads. The action integrations can return instructions on what to do, what’s allowed, info messages to be rendered, new state after the action, AND an entire new provider to start listening to if it “forked” the world (e.g. made a new branch), as well as the priority to give it (highest).

Abstractions therefore must have unique IDs that all providers agree on so they can be joined. These IDs can consist of text, as well as a series of IDs from other abstractions. I.e. a CORE has an ID (#4) but also a host (so you put the host ID as a separate field in the Core ID), and together it uniquely identifies that Core.

VUI downloaded states have names of course, but also have other attributes like “age”. This can help ui_elements explain discrepancies. For example:

1. Config-intent master has name “CONFIG INTENT”, and it’s LIVE
2. Config-intent 1w-ago master has name “CONFIG INTENT”, but it’s 1 week age.
3. Shadow has name “DEPLOYMENT - SHADOW”, and it’s LIVE

So if all three disagree, the CONFIG INTENTs can be grouped together and the state changes can even be graphed.

## VUI Dashboards

A dashboard is just JSON of a set of panels with coordinates and sizes. Panels themselves are also just JSON, describing their panel type (APP) and panel-specific attributes (selected app). Panel types are also just JSON, describing how the ui_elements are laid out and with what data. A panel type can implement various abstraction types, but usually just one is enough (e.g. APP). This means it’ll be “filled” with an App’s data. A ui_element can be as simple as Title or Text with the app_name. app_name will be filled with the abstraction’s data, and if multiple sources provide conflicting abstractions for app_name, ui_element will clearly show it’s indecisive state and default to the dashboard-level “most trusted source ranking.” E.g. if an app changed name recently, the ui_element will clearly show this because a source from the past will disagree. You may click on the ui_element and switch the source it’s using.

example abstraction types: HOST, CORE, APP, THREAD. APPs have HOSTs. COREs have HOSTs. THREADs have APPs, HOSTs and COREs:

- Host
    - Cores
    - Apps
        - Threads (points to all three)

ui_elements must be configured with abstraction_types to look for and a set of fields to look for for each. ui_elements are “native” in that they are not described by JSON. They are coded manually.

ui_elements can be huge. For example, the SEARCH ui_element takes in just an abstraction_type and then allows you to search through all of them that are defined. You can customize the columns that show up. ui_elements can also take in ui_elemenets. For example, the SEARCH ui_element can render desired attributes in each result row as other ui_elements (instead of raw text) at the user’s request. These ui_elements are like any other, taking in an abstraction and doing stuff.

ui_elements can be elementary. For example, the CHILDREN ui_element just takes an parent abstraction_type and a child abstraction_type and renders all children found for a given parent, in whichever way desired (with more ui_elements). Similarly, a PARENT ui_element can be defined to display the single parent (if it exists). CHILDREN is really just PARENT but shows multiple results.

ui_elements can RECURSE. A CHILDREN ui_element can have it’s children abstractions also rendered as CHILDREN ui_elements.

ui_elements can DO stuff. For example, any ui_element that renders multiple ui_elements (e.g. SEARCH or CHILDREN) can be given a movable_abstraction_type, which will allow any ui_element that renders this abstraction_type to be moved around at the level of this ui_element. It also must be given the provider and integration to use to push changes and re-download state.

For a traditional thread layout, you can do:

- SEARCH(host, movable_abstraction_type=”thread”)
    - CHILDREN(host → cores)
        - CHILDREN(core → threads)
            - PARENT(thread → app)

ui_elements should also be able to GRAPH. While using third party providers where possible is encouraged (e.g. Grafana), sometimes the data is just conveniently on VUI.

ui_elements can also create other ui_elements or also create visuals (arrows, text) that are separate to panels.

ui_elements that render other ui_elements do so by first creating JSON with all of the other ui_elements, and then rendering. This only ever gets resolved at a depth of 1 at a time. This allows custom ui_elements to be created in Python very easily - they just have to return JSON with other ui_elements. Create a “true” base ui_element requires JavaScript, but more often than not people will want to make wrappers that interact with their abstractions in a unique way.

All ui_elements need a “config” mode, during which a popup appears so you can configure them. This allows you to fill in their JSON in a more intuitive way.

Custom Python can also be created to automatically create dashboards, panels and arrows.

You should be able to place ui_elements at any x,y coordinate of a panel, and they just float / overlap. Perhaps this can be snapped to 10px.

# VUI mechanisms

There’s the following kinds of VUI ui_elements:

1. Base - take in some JSON and render natively with UI (e.g. Text or Button)
2. Nonbase - take in some JSON and return a bunch more JSON for lots of other UI elements

Positioning:

1. All components have size and position attributes.
2. These are usually relative to the panel or the parent nonbase ui_element (or a sibling ui_element, any really!)

They execute by:

1. Taking in all the current state for all VUIPs for all abstractions
2. Filtering down to just what this ui_element cares about
    1. If this is a base ui_element, it will likely require a specific <abstraction, id> to render.
    2. Each panel has variables, and they get auto-generated with the variables $abstraction_type and $abstraction_id which is also the default that ui_elements will look for
    3. Nonbase ui_elements have more logic to pick, but will usually also default to $abstraction, but the ids tend to be more involved (e.g. grabbing all).
3. Repeat! Until we get just Base.
4. Render!
    1. ui_elements have FIXED dimensions. Some are user-resizable, but they don’t automatically change in size. This makes positioning them easy.
    2. To render positions, since they can be relative, you must resolve them from the leaf nodes first. You must also assert that it’s a DAG, and if there’s a cycle you should just break it by making the position non-relative (or just relative to the panel).
5. Each ui_element has a “refresh” function, which is called whenever new data comes in. At this point, the ui_element must determine if it must rerender or not. We want to be lazy here. Examples:
    1. LIST ui_element only cares if any children have been removed or added. It doesn’t care if their internal data has changed. E.g. if a new one has been added with a new ID, it will re-render.
        1. It gives the children positions relative to the previous child.
    2. Base ui_elements will look at the data inside the abstraction and determine that way. If the abstraction no longer exists, they render an error icon.

Components:

1. Users may create panels and turn them into components, after which they can only change the variables. You can create an “APP” component for example that has the app_name variable.
2. Editing a component occurs in a popup isolated from everything. You may resize it there too. This implies that panels yield their sizing to components, but ofc not their positioning.
3. Components can be “temporary”, which means they’re just generated by ui_elements and they’re not saved to the user’s component directory.
    1. For example, the LIST ui_element creates a single temporary component, which it then instantiates for each abstraction to render.
    2. This makes it easier for the user to resize all children at once. **THINK ABOUT THIS!** 

Variables

1. They must all be unique within any given scope.

Visibility UI
A UI that can visualize our setup, handle alerts, facilitate triaging, and help us make changes.

1. Multi-source
    - Each abstraction (e.g. app) has a list of "sources", e.g. config-intent-staging-branch, config-intent-master-branch, devops-api, shadow, grafana.
    - Each source provides that abstraction with data, e.g. an App get's it's on/off state from shadow, but can get it's underlyings from multiple sources! Some sources could be branches/commits of config-intent from the past, meaning you have competing versions for properties of this abstraction.
2. Physical layout
    - Panels are laid out physically, and arrows can be drawn to connect them. Shapes can also be drawn. This allows you to make rich meaningful dashboards.
    - Dashboards can contain pannels for crossconnects, apps, switches, whatever.
3. ChatGPT-assisted
    - Abstractions & source schemas, alongside UI api, should be sufficiently well-defined such that ChatGPT can write all the UI code to actually create the panels
    - Each panel just has the prompt that was used to create the panel, and the "rendered" prompt output. (Very ambitious, might not be possible).
4. Interconnected
    - Each panel has links to other panels, in such a way that you can get from an MDS to a specific packets that reached a switch in that time less than 5 quick clicks.
    - In some cases, panels may automatically show lines to other panels to show relationships (e.g. APP depends on APP or COMPONENT).
    - Automatic dashboard creation to visualize what an app depends on (it opens all the panels of things it depends on, draws arrows).
    - Also has links to other Optiver resources like ae/ and Grafana
5. Timeline pannel
    - There should be a special panel that displays events over time (possibly live) from a variety of sources that you can pick from. Similar to grafana, but for events. We have something kinda similar, but this would interconnect with the other panels.
6. Functional
    - The UI should be able to do things. E.g. you should be able to move an app around to a different host, and that should generate a config-gen PR.
    - It should also be able to copy a core off a host so you can gdb it
7. Alerting
    - A dedicated alert panel shows current alerts and allows you to quickly open panels or generate dashboards to triage.o



Query LANGUAGE
 1. There's always an implied argument "CONTEXT" of type ObjectList passed in at all times.
 2. All methods receive the CONTEXT and a list of arguments. The arguments can be primitives (e.g. string, dict), SAObjects or they can be other unresolved methods. It is up to the method to resolve child methods, and pass in whatever context it wants to.
 3. All methods start with a . and use () to take in arguments.
 4. An "Expression" is just a list of operators, to be ran in succession. The context of the next is the return value of the previous one.

Example:
.filter(.equals(.get_field("__type__"), "MDS")).get_field("cores").select(.get_field("index"), .get_field("role"))
 - so you get [<filter>(<equals>(<get_field>("__type__"), "MDS")), <get_field>("cores"), <select>(<get_field>("index"), <get_field>("role"), [<get_field>("host"), <get_field>("name")])]
 - filter takes in all its context, groups it across source to get each logical object, and for each one runs the method passed in. On each run, it gets just that ObjectList. it returns an ObjectList
 - equals resolves all methods using all its context and then compares if the resulting primitives are equal, and returns a primite.
 - select takes in infinite arguments, but only expressions starting with operator get_field. It then executes each one and returns a new object with the desired fields replaced with the return value. It removes all other fields. 
 - etc...

A lot of syntactic sugar is required ofc.
.equals is ==
    e.g. .filter(.get_field("__type__") == "MDS")
.get_field is just . without ()
    e.g. .filter(.__type__ == "MDS").cores
.filter is just []
    e.g. *[.__type__ == "MDS"].cores
and the first word is always a filter on __type__
    e.g. mds.cores
.select is {}
    e.g. mds.cores{.index, .role, .host.name}
    or if you want to keep the context of which mds
        e.g. mds{.mds.name, .cores{.index, .role, .host.name}}
    or just
        e.g. mds{.cores{.index, .role, .host.name}} since the id will be persisted in the SAObject

