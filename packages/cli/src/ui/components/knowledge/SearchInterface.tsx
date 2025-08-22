import React, { useState } from 'react';
import { Box, Text, Newline } from 'ink';
import TextInput from 'ink-text-input';
import { KnowledgeDocument } from '../../knowledge/types.js';
import { searchKnowledgeBase } from '../../knowledge/api.js';

interface SearchInterfaceProps {
  onDocumentSelect: (document: KnowledgeDocument) => void;
}

export const SearchInterface: React.FC<SearchInterfaceProps> = ({ onDocumentSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<KnowledgeDocument[]>([]);

  const handleSearch = async () => {
    const searchResults = await searchKnowledgeBase(query);
    setResults(searchResults);
  };

  return (
    <Box flexDirection="column" borderStyle="round" padding={1}>
      <Text>Search Knowledge Base</Text>
      <TextInput value={query} onChange={setQuery} onSubmit={handleSearch} />
      <Newline />
      {results.map((doc) => (
        <Box key={doc.id}>
          <Text>{doc.content}</Text>
        </Box>
      ))}
    </Box>
  );
};
