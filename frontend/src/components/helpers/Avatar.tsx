interface Props {
   role: 'user' | 'assistant';
}

export const Avatar = ({ role }: Props) => {
   return (
      <div
         className={`w-8 h-8 mb-2 rounded-full flex items-center justify-center text-sm font-semibold ${
            role === 'user'
               ? 'bg-gray-400 text-white'
               : 'bg-gray-800 text-white'
         }`}
      >
         {role === 'user' ? 'U' : 'RA'}
      </div>
   );
};
