require 'json'

nodes = {}
links = []

allowedPredicates = ['skos:exactMatch', 'skos:broader', 'skos:narrower', 'skos:relatedMatch', 'skos:mappingRelation']

File.readlines('billings.json').each do |line|
  obj = JSON.parse line

  subject = obj['subject']
  predicate = obj['predicate']
  objectUri = obj['objectUri']

  # skip literals:
  next if objectUri.nil?

  # skip metadata statements; only interested in links
  next if ! allowedPredicates.include? predicate

  objectNamespace = objectUri.split(':')[0] if ! objectUri.nil?
  subjectNamespace = subject.split(':')[0]
  
  nodes[{ "id" => subject, "group" => subjectNamespace }] = 1
  links << { "source" => subject, "target" => objectUri, "value" => allowedPredicates.index(predicate) }
  nodes[{ "id" => objectUri, "group" => objectNamespace }] = 1
end

json = { "nodes" => [], "links" => [] }
json['nodes'] = nodes.keys
json['links'] = links

File.open('./graph/billi.json', 'w') do |f|
  f.write json.to_json
end
